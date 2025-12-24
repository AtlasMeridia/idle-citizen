# Test Document for mdextract

This is a sample markdown file with various code blocks.

## Python Examples

Here's a simple Python function:

```python
def hello(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(hello("World"))
```

And another Python snippet for data processing:

```python
import json

def load_config(path: str) -> dict:
    with open(path) as f:
        return json.load(f)
```

## JavaScript Examples

Here's some JavaScript:

```javascript
const greet = (name) => {
    return `Hello, ${name}!`;
};

export default greet;
```

## Shell Scripts

A useful bash one-liner:

```bash
#!/bin/bash
find . -name "*.md" -exec grep -l "TODO" {} \;
```

## Configuration Files

Example YAML config:

```yaml
name: my-project
version: 1.0.0
dependencies:
  - python: ">=3.9"
  - node: ">=18"
```

And some JSON:

```json
{
  "name": "test",
  "scripts": {
    "build": "tsc",
    "test": "jest"
  }
}
```

## Code without language hint

This block has no language specified:

```
This is just plain text
in a fenced block
```

That's all the examples!
