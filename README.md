# bitcoincoding.dev

The bookshelf at the root of bitcoincoding.dev. Each book is its own repository, published with
GitHub Pages under `bitcoincoding.dev/<repo-name>/`; this repository only holds the shelf page,
short aliases (`/taproot/`, `/from-scratch/`) and redirects for old URLs.

To add a book: publish its repo with GitHub Pages (no CNAME of its own), then copy one
`<article class="book">` block in `index.html` and point it at `/<repo-name>/`.
