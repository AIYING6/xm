# Static fault, legal-task and radio graph separation

`G_task_0` is the static directed legal support graph. A deterministic structural mask creates `G_task_f = G_task_0 ⊙ M_f`. `G_radio_t` contains only distance/LOS/dropout/radio availability. Active communication is `G_active_t,f = G_task_f ⊙ G_radio_t`.

The fault mask is applied before packet creation, cache update and graph-message construction. A dynamic radio outage cannot be relabeled as a structural fault; conversely, a structurally masked edge cannot leave cached/new messages available merely because radio connectivity is good.
