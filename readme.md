# Keeper

Simple python script to download (and upload) your Google Keep notes to your local drive in plain text.

## Requirements

- Create [Google App Password](https://support.google.com/accounts/answer/185833?hl=en)
- Create `config.ini` file at root with:

  ```
  [credentials]
  username = YOUR_GOOGLE_USERNAME
  password = YOUR_GOOGLE_APP_PASSWORD

  [paths]
  notes_root = YOUR_OUPUT_PATH
  ```

## Installation

```
pipenv install
```

## Use

```
pipenv run python keep.py --download
pipenv run python keep.py --upload
```
