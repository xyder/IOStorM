# DB Structure

---

### tag
###### Contains a set of hierarchies of tags represented by materialized paths.

Column | Type | Description
--- | :---: | ---
uid | int | identifier <a name="tag-uid" />
user_id | fk | [user.uid](#user-uid)
path | ltree | path to the tag itself containing the tag label. auto-generated on creation
position | int | position under the parent. updates on move/insert etc
title | str | this title will be used in human readable paths. can contain any char except '/' which is used as sep
description | str | description of the tag

---

### bookmark
###### Contains information about bookmarks.

Column | Type | Description
--- | :---: | ---
uid | int | identifier <a name="bookmark-uid" />
place_id | fk | [places.uid](#place-uid)
user_id | fk | [user.uid](#user-uid)
title | str | title of the bookmark
description | str | description of the bookmark

---

### bookmark_property
###### Properties that a bookmark might have.

Column | Type | Description
--- | :---: | ---
uid | int | identifier <a name="bookmark_property-uid" />
bookmar_id | fk | [bookmark.uid](#bookmark-uid)
key | str | ex: rating,
value | str
value_type | str | ex: str, int, bool

---

### bookmark_tag
###### Associations between bookmarks and tags.

Column | Type | Description
--- | :---: | ---
bookmark_id | fk | [bookmark.uid](#bookmark-uid)
tag_id | fk | [tag.uid](#tag-uid)
position | int | position under parent. updates on move/insert etc
--- | pk | bookmark_id, tag_id

---

### tag_list_definition
###### Contains the definitons of tag lists.

Column | Type | Description
--- | :---: | ---
uid | int | identifier <a name="tag_list_definition-uid" />
name | str | name of the list
user_id | fk | [user.uid](#user-uid)

---

### tag_list_item
###### Contains associations between lists and the tags in them.

Column | Type | Description
--- | :---: | ---
tag_id | fk | [tag.uid](#tag-uid) - tag that belongs to the list
tag_list_id | fk | [tag_list_definition.uid](#tag_list_definition-uid) - id of the list
--- | pk | tag_id, tag_list_id

---

### favicon

Column | Type | Description
--- | :---: | ---
uid | int | identifier <a name="favicon-uid" />
data | bytes | contains the favicon data
mime_type |
expiration |  | date when the favicon should be refreshed

---

### preview
###### Contains filepaths to previews of web pages.

Column | Type | Description
--- | :---: | ---
uid | int | identifier - previews will be stored as: preview_folder/<uid>.ext <a name="preview-uid" />
user_id | fk | [user.uid](#user-uid)
place_id | fk | [place.uid](#place-uid)
expiration | timestamp | date when the preview should be refreshed

---

### place 
###### Min store for URLs.

Column | Type | Description
--- | :---: | ---
uid | int | identifier <a name="place-uid" />
scheme | str | ex: `http`/`https`/`ftp` .. default is `http` unless alt_url is specified
authority | str | ex: `user:pass@www.example.com`
path | str | ex: `subpath1/subpath2/file.html`
query | str | ex: `a=1&b=2&c=3`  (`?` implied)
fragment | str | ex: `top` (`#` implied)
alt_url | str | anything else that does not conform to the standard url syntax
favicon_id | fk | [favicon.uid](#favicon-uid)

---

### user

Column | Type | Description
--- | :---: | ---
uid | int | identifier <a name="user-uid" />
user_name | str | login name
first_name | str |
last_name | str |
key_hash | bytes | hashed password for authentication

---

### user_property

Column | Type | Description
--- | :---: | ---
uid | int | identifier <a name="user_property-uid" />
user_id | fk | [user.uid](#user-uid)
key | str |
value | str |
value_type | str | str ex: str, int, bool
