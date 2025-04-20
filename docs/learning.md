# 🧙‍♂️ Python: Learning Discoveries

> Just a few notes on what I've learned while working on this project. I hope you find them useful! \
> Trying to get better about documentation in general but I'll keep this short and sweet.

## 🔮 Default Argument Evaluation

### Patch Not Patching?

I was working on debugging a test for `load_project_config` in the `Config` class. The original code looked like this:

```python
# ❌ BEWARE THIS SPELL! It contains hidden magic!
@staticmethod
def load_project_config(config_dir:Path = Path.cwd()) -> dict:
    """Load local project configuration"""
    local_config_path = config_dir / "canvas.json"
    if local_config_path.exists():
        with open(local_config_path, "r") as f:
            return json.load(f)
    else:
        return None
```

When you try to test this function by patching `Path.cwd()`, your test mysteriously fails! Why?

### Argument Evaluation in Python

**In Python, default arguments are evaluated ONCE at function definition time, not each time the function is called!**

This means `Path.cwd()` is executed when the Python interpreter first reads your code - long before your patch is applied!

### 🌟 The Solution

Always use `None` as your default value when the default involves a function call, then evaluate inside the function:

```python
# ✅ THE PROPER INCANTATION:
@staticmethod
def load_project_config(config_dir: Path = None) -> dict:
    """Load local project configuration"""
    if config_dir is None:
        config_dir = Path.cwd()  # Only now is Path.cwd() called!

    ...
```

Now your magical tests can properly patch `Path.cwd()` because it gets called each time the function runs!

---