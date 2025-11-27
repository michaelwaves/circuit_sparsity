from circuit_sparsity.inference.gpt import GPT, GPTConfig, load_model
from circuit_sparsity.inference.hook_utils import hook_recorder
from circuit_sparsity.registries import MODEL_BASE_DIR
from torch import tensor, randint


batch = 1
seq_len = 8
vocab_size = 16
idx = tensor([[1, 5, 7, 3, 2, 9, 14, 4]])
idx = randint(low=0, high=vocab_size, size=(batch, seq_len))
print(f"Token Ids {idx}")

targets = idx.clone()
targets[:, :-1] = idx[:, 1:]
targets[:, -1] = -1
print(f"Targets: {targets}")
config = GPTConfig(block_size=8, vocab_size=16, n_layer=1, n_head=1, d_model=8)
model = GPT(config)

print(model)
print(model.transformer.drop)
logits, loss, mystery = model(idx, targets=targets)
print(logits.shape)
print(loss.shape)
print(len(mystery))

pretrained_model = load_model(f"{MODEL_BASE_DIR}/models/csp_yolo2")
