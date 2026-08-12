"""Static guards for IA9 replay."""
from pathlib import Path
def main():
 s=Path(__file__).with_name('run_phase2ia9_path_replay.py').read_text(encoding='utf8')
 assert 'SEEDS=(801,802,803)' in s and 'run_one(c,ci,s,si,ep)' in s and 'TRACE_ONLY_PATH_AUDIT' in s and 'Refusing to overwrite' in s
 assert 'checkpoint' not in s and 'optimizer' not in s
 print('PHASE2IA9_PATH_REPLAY_TEST=PASS')
if __name__=='__main__':main()
