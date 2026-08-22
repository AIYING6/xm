"""Explicit stochastic streams for the DRTP seed-causal diagnostic.

The historical training path intentionally remains legacy-compatible when
``rng_decomposition`` is disabled.  S1 runs opt in to this module so that
initialization, environment, action, minibatch, topology, and evaluation
randomness have independently derived seeds and cannot be coupled through a
shared global RNG by construction.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import asdict, dataclass

import numpy as np
import torch


STREAM_NAMES = (
    "init",
    "env",
    "action",
    "minibatch",
    "topology",
    "eval",
)


@dataclass(frozen=True)
class RNGSeedTuple:
    init_seed: int
    env_seed: int
    action_seed: int
    minibatch_seed: int
    topology_seed: int
    eval_seed: int

    def validate(self) -> None:
        values = asdict(self)
        if set(values) != {f"{name}_seed" for name in STREAM_NAMES}:
            raise ValueError("RNG seed tuple does not cover all frozen streams")
        if any(int(value) < 0 for value in values.values()):
            raise ValueError("RNG stream seeds must be non-negative")


def _derive_seed(base: int, stream: str, *components: int) -> int:
    if stream not in STREAM_NAMES:
        raise ValueError(f"unknown RNG stream: {stream}")
    payload = ":".join([str(int(base)), stream, *(str(int(value)) for value in components)])
    digest = hashlib.blake2b(payload.encode("ascii"), digest_size=8).digest()
    return int.from_bytes(digest, "little") & 0x7FFFFFFF


class RNGStreams:
    """Independent deterministic RNG factories bound to one seed tuple."""

    def __init__(self, seeds: RNGSeedTuple):
        seeds.validate()
        self.seeds = seeds

    @classmethod
    def from_master(cls, master_seed: int) -> "RNGStreams":
        master = int(master_seed)
        return cls(
            RNGSeedTuple(
                init_seed=_derive_seed(master, "init"),
                env_seed=_derive_seed(master, "env"),
                action_seed=_derive_seed(master, "action"),
                minibatch_seed=_derive_seed(master, "minibatch"),
                topology_seed=_derive_seed(master, "topology"),
                eval_seed=_derive_seed(master, "eval"),
            )
        )

    def seed(self, stream: str, *components: int) -> int:
        if stream not in STREAM_NAMES:
            raise ValueError(f"unknown RNG stream: {stream}")
        base = int(getattr(self.seeds, f"{stream}_seed"))
        return _derive_seed(base, stream, *components)

    def python_rng(self, stream: str, *components: int) -> random.Random:
        return random.Random(self.seed(stream, *components))

    def numpy_rng(self, stream: str, *components: int) -> np.random.Generator:
        return np.random.default_rng(self.seed(stream, *components))

    def torch_generator(self, stream: str, device: torch.device | str = "cpu", *components: int) -> torch.Generator:
        device_obj = torch.device(device)
        generator = torch.Generator(device=device_obj.type)
        generator.manual_seed(self.seed(stream, *components))
        return generator

    def manifest(self) -> dict:
        return {
            "format": "drtp_seed_s1_rng_tuple_v1",
            "streams": list(STREAM_NAMES),
            "seeds": asdict(self.seeds),
            "derivation": "blake2b(base_seed, stream_name, components) -> signed-31-bit seed",
            "global_rng_coupling": "disabled for S1 opt-in action/minibatch/environment configuration paths",
        }

    def probe(self) -> dict[str, list[float | int]]:
        """Return deterministic values used by the one-factor isolation test."""
        return {
            "init": [self.seed("init"), *self.numpy_rng("init").integers(0, 2**31, size=3).tolist()],
            "env": [self.seed("env"), *self.numpy_rng("env").random(3).tolist()],
            "action": [self.seed("action"), *self.numpy_rng("action").random(3).tolist()],
            "minibatch": [self.seed("minibatch"), *self.numpy_rng("minibatch").permutation(8).tolist()],
            "topology": [self.seed("topology"), *self.numpy_rng("topology").integers(0, 7, size=3).tolist()],
            "eval": [self.seed("eval"), *self.numpy_rng("eval").random(3).tolist()],
        }

