# generated-file-header

Every file listed in the `targets:` field of a `.spec.md` must begin with this header:

For Python files:
```python
# GENERATED FROM SPEC — DO NOT EDIT DIRECTLY
# Source: specs/<spec-name>.spec.md
```

For JavaScript/TypeScript files:
```js
// GENERATED FROM SPEC — DO NOT EDIT DIRECTLY
// Source: specs/<spec-name>.spec.md
```

For other file types, use the appropriate comment syntax.

Add the header as the very first line(s) of the file (after shebang or doctype if present) before writing any other content. Replace `<spec-name>` with the actual spec filename.
