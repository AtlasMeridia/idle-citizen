# ollama-bench

Benchmark Ollama models for response time and token generation speed.

Useful for comparing models when building local AI applications like DAEMON.

## Usage

```bash
# List available models
ollama-bench list

# Benchmark a single model with default prompts
ollama-bench run qwen2.5:7b

# Benchmark with a custom prompt
ollama-bench run qwen2.5:7b "Explain quantum computing in one sentence"

# Compare multiple models
ollama-bench compare qwen2.5:7b llama3.2:3b mistral:7b

# Output as JSON (for scripting)
ollama-bench compare qwen2.5:7b llama3.2:3b --json

# Verbose output with per-prompt details
ollama-bench compare qwen2.5:7b llama3.2:3b -v
```

## Metrics

- **First Token**: Time to first token (measures model load + initial inference)
- **Total Time**: Total response time
- **Tokens/sec**: Approximate generation speed

## Example Output

```
Model Comparison
======================================================================
Model                          First Token      Total    Tok/s
----------------------------------------------------------------------
qwen2.5:7b                           892ms     3421ms     15.2
llama3.2:3b                          342ms     1876ms     22.1
mistral:7b                           756ms     2943ms     14.8
```

## Notes

- First run of each model includes model loading time
- Tool does a warm-up run to pre-load the model before benchmarking
- Token count is estimated (4 chars per token)
- Requires Ollama to be running locally

## Installation

No dependencies beyond Python 3. Just make it executable:

```bash
chmod +x ollama-bench.py
./ollama-bench.py list
```

Or run with Python:

```bash
python3 ollama-bench.py list
```
