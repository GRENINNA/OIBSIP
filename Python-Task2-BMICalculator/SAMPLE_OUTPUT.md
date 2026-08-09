# BMI Calculator - Sample Output

This file contains representative demonstration output. It does not contain
real personal health information.

## Example calculation

```text
Name: Demo User
Weight: 70 kg
Height: 1.75 m

BMI: 22.86
Category: Normal
Display colour: Green
```

Calculation:

```text
BMI = 70 / (1.75 x 1.75)
BMI = 22.857...
Displayed BMI = 22.86
```

## Example history table

| Recorded | Weight | Height | BMI | Category |
| --- | ---: | ---: | ---: | --- |
| 09 Aug 2026, 10:30 | 70.00 kg | 1.75 m | 22.86 | Normal |
| 02 Aug 2026, 10:15 | 72.00 kg | 1.75 m | 23.51 | Normal |
| 26 Jul 2026, 09:55 | 74.00 kg | 1.75 m | 24.16 | Normal |

## Expected validation messages

```text
Weight and height must be numeric values (for example, 70 and 1.75).
Weight must be greater than 0 kg.
Height must be greater than 0 m.
Enter a name before saving or viewing history.
```

## Trend output

Selecting **View BMI trend** opens a line chart of saved BMI values. The app
uses Matplotlib when available and automatically uses its built-in Tkinter
chart otherwise.

