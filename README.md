# CharZapper

## Description

CharZapper is a character map snippet engine.

CharZapper allows you to type unicode symbols
easily into documents using different matching patterns.  For example, opening CharZapper
and typing "pi" will allow you to type the pi symbol itself into your document.

There are two usages of CharZapper:

1. Using CharZapper to paste the symbol into your clipboard, and then manually pasting it.
2. Triggering CharZapper using a hotkey and auto-pasting the selected symbol. 

The auto-paste script is only supported on Windows, but CharZapper itself is cross-platform.

CharZapper uses a few different matching strategies to determine what you are intending to type,
so you don't have to remember the exact name of the symbol.  It can also be used to combine characters
to create symbols, much like a compose key would do.

## (Optional) Activating via a Hotkey on Windows

This project includes an AutoHotkey script called `CharZapper.ahk` which can
be used to trigger the application using the Apps/Menu key on your keyboard
and paste the result into your open program.  This allows you to easily type
symbols into the program you're already typing in.

You can configure the script to use the right python directory for your system
as well as changing the hotkey if you wish.

Once the script is running, by pressing your hotkey, CharZapper will start.
You can then select a symbol.  Pressing enter will close CharZapper and paste
the snippet into the program you have open beneanth.

## Installation

First, Install python for your system.

Then, install the dependencies using the below command or by installing each library found in the `requirements.txt` file.

```
pip -r requirements.txt
```

You may need to execute the above command with Admin permissions.

To use the auto-paste script, you must install AutoHotkey.

## Basic Usage

Open CharZapper.py and start by typing "->".
You'll notice an arrow appears above.  When you hit enter, the symbol will be copied
into your clipboard.

Some symbols appear in both upper and lower case.  Hold the shift key inside CharZapper
while you hit ENTER to change the case, or type your input text in uppercase.

## Auto-Paste Usage

Run CharZapper.ahk using AutoHotkey.  Open notepad and press the Menu/Apps key.
CharZapper should start.  Now type "theta".  You should see a theta symbol appear.
Hit enter and it will be pasted into your notepad document.

Note: You'll need to use a font that supports the symbols you wish to use.

## Examples

(Based on your current font, you may not be able to view the below symbols)

- theta: θ
- inf: ∞
- sum: ∑

See `snippets.yaml` for more.

## Customization

The program uses a snippets dictionary called `snippets.yaml` which can be
customized to include your own snippets and symbols.

## How it Works

Here are CharZapper's matching strategies:

- Exact Match: CharZapper matches a name with its symbol in the database.
- Keyword/tag Match: Symbols can match specific keywords that categorize the symbol, such as "equal".
- Character Match: Specific characters when combined will trigger a combined symbol, such as 'co' for
the copyrght symbol.

