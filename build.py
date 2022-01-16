def build():
    try:
        # try to compile cyk.py if mypy is installed
        from mypyc.build import mypycify

        return {"ext_modules":  mypycify(["darglint/parse/cyk.py"])}
    except ImportError:
        return {}
