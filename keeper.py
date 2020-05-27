import os
import pathlib
import configparser

import keyring
import gkeepapi

NOTE_FILE_EXTENSION = '.txt'
LIST_FILE_EXTENSION = '.todo'

class Keeper:

  def __init__(self):
    self.keep = gkeepapi.Keep()
    self.config = configparser.ConfigParser()
    self.config.read('config.ini')
    self.username = self.config['credentials']['username']
    self.password = self.config['credentials']['password']
    self.notes_root = pathlib.Path(self.config['paths']['notes_root'])
    self.token = keyring.get_password('google-keep-token', self.username)

    if not self.token:
      self.login(self.username, self.password)
    else:
      self.resume(self.username, self.token)

  def resume(self, username, token):
    self.keep.resume(username, token)

  def login(self, username, password):
    self.keep.login(username, password)
    self.token = self.keep.getMasterToken()
    keyring.set_password('google-keep-token', username, self.token)

  def download(self):
    gnodes = self.keep.all()
    for gnode in gnodes:
      is_list = (gnode._TYPE == gkeepapi.node.NodeType.List)
      self._save_locally(gnode, is_list)

  def upload(self):
    added = []
    deleted = []

    for fpath in self._get_list_filepaths():
      lf = self._get_id_title_by_filepath(fpath)
      glist = self.keep.get(lf['id'])

      with open(fpath, 'r', encoding='utf-8') as file:
        for line in file:
          if len(line) < 5 or line[1] != '[':
            continue

          checkmark = line[1:4].strip()
          checkmark_checked = (checkmark == "[x]")
          text = line[5:].strip()

          remote_matching_items = list(filter(lambda i: i.text.strip() == text, glist.items))
          if len(remote_matching_items) > 0:
            gitem = remote_matching_items[0]
            if gitem.checked != checkmark_checked:
              print("[sync]: update checkmark found at: {}\n{}".format(fpath, line.strip()))
              gitem.checked = checkmark_checked
          else:
            print("[sync]: adding item found at: {}\n{}".format(fpath, line.strip()))
            glist.add(text, checkmark_checked, gkeepapi.node.NewListItemPlacementValue.Top)

      self.keep.sync()


  def _get_list_filepaths(self):
    return [f for f in self.notes_root.iterdir() if f.suffix == LIST_FILE_EXTENSION]

  def _get_filepath_by_id(self, id):
    for file in self.notes_root.iterdir():
      nodet = self._get_id_title_by_filepath(file)
      if nodet['id'] == id:
        return file
    return "not found!"

  def _get_filepath_by_title(self, title):
    for file in self.notes_root.iterdir():
      nodet = self._get_id_title_by_filepath(file)
      if nodet['title'] == title:
        return file
    return "not found!"

  def _get_id_title_by_filepath(self, fpath):
    with open(fpath, 'r', encoding='utf-8') as gfile:
      lines = gfile.readlines()[-3:]

      separator = lines[0].strip()
      id = lines[1].strip()[7:]
      title = lines[2].strip()[7:]

      if separator == '---':
        return { 'id': id, 'title': title }

      return { 'id': '', 'title': '' }

  def _save_locally(self, gnode, is_list):
    gnode_fpath = self._get_gnode_filepath(gnode, is_list)

    with open(gnode_fpath, 'w+', encoding='utf-8') as gfile:
      if is_list:
        if gnode.title:
          title = "{}:\n".format(gnode.title)
          gfile.write(title)

        for gitem in gnode.unchecked:
          item = " [ ] {}\n".format(gitem.text)
          gfile.write(item)

        for gitem in gnode.checked:
          item = " [x] {}\n".format(gitem.text)
          gfile.write(item)

      else:
        gfile.write(gnode.text)

      gfile.write(self._generate_footer(gnode.title, gnode.id))

  def _get_gnode_filepath(self, gnode, is_list):

    if not gnode.title:
      fpath_wo_suffix = self.notes_root / gnode.id
    else:
      fpath_wo_suffix = self.notes_root / self._get_trimmed_name(gnode.title)

    file_ext = LIST_FILE_EXTENSION if is_list else NOTE_FILE_EXTENSION
    fpath = fpath_wo_suffix.with_suffix(file_ext)

    fpath = self._ensure_filename_is_unique(fpath, gnode, 1)

    return fpath

  def _get_trimmed_name(self, title):
    name = title
    name = name.replace('/', '_')
    name = name.replace('?', '_')
    name = name.replace(':', '_')
    name = name.replace(' ', '_')
    name = name.lower()
    return name

  def _ensure_filename_is_unique(self, fpath, gnode, number):

    if fpath.exists():
      fnode = self._get_id_title_by_filepath(fpath)
      if fnode['id'] == gnode.id and fnode['title'] == gnode.title:
        return fpath

      fname = fpath.stem
      if fname[-2] == '_' and fname[-1].isnumeric():
        fname = fname[:-2]
      fpath = fpath.with_name("{}_{}{}".format(fname, number, fpath.suffix))
      return self._ensure_filename_is_unique(fpath, gnode, number+1)

    return fpath

  def _generate_footer(self, title, id):
    return "\n\n---\nid:    {}\ntitle: {}".format(id, title)

  def _rename_existing_filename(self, fpath, number):
    fname = fpath.stem
    if fname[-2] == '_' and fname[-1].isnumeric():
      fname = fname[:-2]
    fpath = fpath.with_name("{}_{}{}".format(fname, number, fpath.suffix))

    if fpath.exists():
      fpath = self._rename_existing_filename(fpath, number+1)
    return fpath
