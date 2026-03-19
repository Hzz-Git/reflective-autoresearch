# Beliefs

1. [confidence: med] Larger models generally achieve lower val_bpb given sufficient training time — common knowledge, not yet tested in this setup
2. [confidence: med] Learning rate is the most sensitive hyperparameter for short 5-minute runs — common knowledge
3. [confidence: low] Batch size changes trade throughput for gradient noise — textbook prior
4. [confidence: low] Architectural changes (depth vs width) may have outsized effects under fixed time budget — untested hypothesis
5. [confidence: low] Optimizer choice interacts strongly with learning rate schedule — untested hypothesis
