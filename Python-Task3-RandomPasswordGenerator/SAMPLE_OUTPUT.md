# Random Password Generator - Sample Output

This output is for demonstration only. Never use a password published in source
code, documentation, screenshots, or videos for a real account.

## Example settings

```text
Length: 16 characters
Uppercase letters: Included
Lowercase letters: Included
Numbers: Included
Symbols: Included
Exclude ambiguous characters: Enabled
```

## Representative result

```text
Generated password: [REDACTED DEMONSTRATION PASSWORD]
Strength: Strong
Clipboard: Copied automatically
```

The actual password changes every time because generation uses Python's
cryptographically secure `secrets` module.

## Example validation messages

```text
Password length must be between 8 and 128 characters.
Select at least two character types.
Password length must be a whole number.
```

## Session-history behavior

```text
History entries displayed: Last 5 generated passwords
Persistence: Memory only
History after application closes: Erased
```

