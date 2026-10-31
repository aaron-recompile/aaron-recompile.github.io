"""Build the research and experiment pages, llms.txt and sitemap.xml.

Each page has two layers: the HTML a person reads, and a machine layer
(JSON-LD in the head, plus a facts.json next to the page) carrying the same
claims as structured data. Run from the repo root:

    python3 tools/build_pages.py

Glyphs are read from index.html (the card whose title links to the page), so
the homepage card and the page header always show the same picture.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://bitcoincoding.dev"
PERSON_ID = f"{SITE}/#aaron"
MEMPOOL = "https://mempool.space/signet/tx/"
GH = "https://github.com/aaron-recompile/"

# Wikidata items checked by hand (MB676 entity work); only these are used.
THING = {
    "bitcoin": {"@type": "Thing", "name": "Bitcoin", "sameAs": "https://www.wikidata.org/wiki/Q131723"},
    "taproot": {"@type": "Thing", "name": "Taproot", "sameAs": "https://www.wikidata.org/wiki/Q107377077"},
    "script": {"@type": "Thing", "name": "Bitcoin Script", "sameAs": "https://www.wikidata.org/wiki/Q96472816"},
    "schnorr": {"@type": "Thing", "name": "Schnorr digital signature scheme", "sameAs": "https://www.wikidata.org/wiki/Q1465057"},
}

ICON_GH = '<svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 .5a11.5 11.5 0 0 0-3.64 22.41c.58.1.79-.25.79-.56v-2c-3.2.7-3.88-1.37-3.88-1.37-.53-1.33-1.29-1.69-1.29-1.69-1.05-.72.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.77 2.71 1.26 3.37.96.1-.75.4-1.26.73-1.55-2.55-.29-5.24-1.28-5.24-5.69 0-1.26.45-2.29 1.19-3.1-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.17 1.18a11 11 0 0 1 5.77 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.76.11 3.05.74.81 1.19 1.84 1.19 3.1 0 4.42-2.7 5.39-5.26 5.68.41.36.78 1.06.78 2.14v3.17c0 .31.21.67.8.56A11.5 11.5 0 0 0 12 .5Z"/></svg>'
ICON_TALK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M4 5h16v11H9l-5 4z"/></svg>'
ICON_DOC = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M6 2h9l5 5v15H6z"/><path d="M14 2v6h6"/></svg>'


def tx(role, txid, block=None, note=""):
    return {"role": role, "txid": txid, "block": block, "note": note}


EXPERIMENTS = [
    {
        "slug": "experiments/eltoo-apo-ctv",
        "kind": "Builds on Christian Decker · eltoo",
        "title": "APO from scratch: a BIP-118 signer and an eltoo state chain",
        "card_title": "APO from scratch, then an eltoo chain",
        "date": "2026-04-11",
        "description": "An independent BIP-118 (ANYPREVOUT) signer, written outside Bitcoin Core's test framework and cross-validated by Inquisition's consensus code, then used to run a three-round eltoo state chain settled with CTV.",
        "lede": "Two steps. First the primitive: an independent BIP-118 (ANYPREVOUT) signer, written outside Bitcoin Core's test framework and cross-validated by Inquisition's consensus code, with an on-chain proof that one signature spends two coins. Then the construction: a three-round eltoo state chain built on it and settled with OP_CHECKTEMPLATEVERIFY.",
        "about": ["bitcoin", "taproot", "script", "schnorr"],
        "keywords": ["SIGHASH_ANYPREVOUT", "BIP 118", "Msg118", "eltoo", "LN-Symmetry", "OP_CHECKTEMPLATEVERIFY", "BIP 119", "Bitcoin Inquisition"],
        "question": [
            "Eltoo, proposed by Christian Decker, Rusty Russell and Olaoluwa Osuntokun, lets a payment channel replace its state instead of punishing old states. Its enabling primitive is <code>SIGHASH_ANYPREVOUT</code> (BIP 118): a signature that does not commit to the coin it spends.",
            "Bitcoin Core's wallet and command line cannot produce such a signature, so anyone who wants to exercise APO on Inquisition signet has to build the signer first. Following ajtowns' survey of CTV, APO and CAT activity on signet, this work adds that missing piece and then uses it end to end.",
        ],
        "parts": [
            {
                "label": "Part 1 · The primitive",
                "title": "A BIP-118 signer, cross-validated by consensus",
                "paras": [
                    "The signing message Msg118 / Ext118 and the final <code>TaggedHash(\"TapSighash\", 0x00 || Msg118 || Ext118)</code> are implemented in Python straight from the BIP, outside Bitcoin Core's test framework. Inquisition's C++ consensus code rebuilds the same digest from the transaction; if the two disagree by one byte, the transaction is rejected.",
                    "What BIP 118 changes is what the message leaves out:",
                ],
                "table": (["Field", "BIP 342 (SigMsg)", "BIP 118 (Msg118, 0x41)"], [
                    ["nVersion, nLockTime", "yes", "yes"],
                    ["sha_prevouts (which coins are spent)", "yes", "<strong>no</strong>"],
                    ["sha_sequences", "yes", "<strong>no</strong>"],
                    ["input amount and scriptPubKey", "yes", "yes"],
                    ["sha_outputs", "yes", "yes"],
                    ["tapleaf_hash", "yes", "yes"],
                    ["key_version", "0x00", "<strong>0x01</strong>"],
                ]),
                "after": "The outpoint drops out of the digest, and key_version 0x01 separates the signature domain so an APO signature cannot be replayed against an ordinary key.",
                "proof_title": "On-chain proof: one signature, two coins",
                "proof": "Two 50,000-sat UTXOs at the same address, under a single-leaf tapscript <code>&lt;0x01||xonly&gt; OP_CHECKSIG</code>. The first spend is signed; its whole witness (a 65-byte signature ending in 0x41, the 35-byte leaf, the 33-byte control block) is copied byte for byte onto a second transaction spending the other coin. Both confirmed in the same block. Changing the output address or amount in the second spend makes it fail: the input can be rebound, the destination cannot.",
                "txs": [
                    tx("Spend A (signed)", "03c0577c1d47da32804d098187644d0eee18b448aded2f427cd02193c070f3a4", 298280, "prevout 4b645108…:0"),
                    tx("Spend B (witness copied, not re-signed)", "46091190c74d8fd4b39be67a2e945a19b021850e7f8d9e378f5eb11722ae1a43", 298280, "prevout 543c97f7…:0"),
                ],
            },
            {
                "label": "Part 2 · The construction",
                "title": "A three-round eltoo state chain",
                "paras": [
                    "With the signer in hand, every channel state becomes a three-leaf Taproot output. An APO update spends the current state and creates the next; the spent state's CTV leaf loses its only input and can never settle, so only the latest state can pay out. That is the eltoo invariant, executed end to end with current tooling.",
                ],
                "how": "each state UTXO (P2TR, three leaves)\n\n  ctv_settle   <template_hash> OP_CHECKTEMPLATEVERIFY       # this state's payout\n  apo_update   <0x01 || xonly_pubkey> OP_CHECKSIG          # next state replaces this one\n  csv_escape   <2> OP_CHECKSEQUENCEVERIFY OP_DROP <pk> OP_CHECKSIG\n\nfund -> v1 -> v2 -> v3   (two APO updates)\nsettle v3 through ctv_settle: witness = script + control block, empty stack",
                "txs": [
                    tx("Fund → state v1", "386dbb6aa23fcc35a69d34e3c0f760b185482467abc936196d3def19d54a9c41", 298059, "50,000 sats"),
                    tx("APO update v1 → v2", "096e31ccbd8f5460b2730ec4f757ee1b01acf9dde3e3b8cb55fbb534fe195601", 298280, "47,000 sats"),
                    tx("APO update v2 → v3", "091309b73e299436ff12fceda7e54e28c6f1817fdf3405bca3343ad15198d7f6", 298280, "44,000 sats"),
                    tx("CTV settlement of v3", "13957f49d01aa21ed2aa28df7aa78f357d51a2a2fbfb434af05fdc75ad0ff9b7", 298280, "16,400 / 14,350 / 10,250 sats"),
                ],
                "after": "The two rebinding transactions in Part 1 are a standalone demonstration, not part of this chain.",
            },
        ],
        "repo": "eltoo-apo-state-chain",
        "code_links": [
            ("BIP-118 signer · btcaaron/bip118.py", "https://github.com/aaron-recompile/btcaaron/blob/180935dc864c9a36dd725cf8f54a43d183c17b1a/btcaaron/bip118.py"),
            ("Tests: digest invariance and signing", "https://github.com/aaron-recompile/btcaaron/blob/180935dc864c9a36dd725cf8f54a43d183c17b1a/tests/test_bip118.py"),
        ],
        "verify": {"command": "python3 verify_onchain.py", "result": "37/37 checks passed", "needs": "no keys, no node: it recomputes the BIP-118 digest for every APO signature"},
        "not_shown": [
            "No Lightning protocol stack: no BOLT messaging, two-node exchange or HTLC routing.",
            "The CSV timeout leaf is committed in every state but was not exercised.",
            "One demo key signs every update; no FROST or MuSig2 aggregation.",
            "Updates run sequentially; this is the execution layer underneath a channel, not a channel implementation.",
        ],
        "discussion": [
            ("Delving Bitcoin · BIP 118 signing from scratch + on-chain rebinding proof (Part 1)", "https://delvingbitcoin.org/t/2411"),
            ("Delving Bitcoin · Eltoo State Chain on Signet: Three Rounds, Six Transactions (Part 2), with a reply from Christian Decker", "https://delvingbitcoin.org/t/2413"),
            ("bitcoindev mailing list · Eltoo / LN-Symmetry on Inquisition Signet: BIP 118 + 3-Round State Chain, with replies from Greg Sanders and Sergio Demian Lerner", "https://mailing-list.bitcoindevs.xyz/bitcoindev/CAEmKuUHJEf8R0ZPa--Jm=e1ToT2-f1CUqp+dRLP=XZ+A3mLBzA@mail.gmail.com/"),
        ],
        "sources": [
            ("BIP 118: SIGHASH_ANYPREVOUT for Taproot Scripts", "https://github.com/bitcoin/bips/blob/master/bip-0118.mediawiki"),
            ("ajtowns · CTV, APO, CAT activity on signet", "https://delvingbitcoin.org/t/ctv-apo-cat-activity-on-signet/1257"),
        ],
        "post": "https://delvingbitcoin.org/t/2411",
        "onchain": 6,
    },
    {
        "slug": "experiments/prevout-binding",
        "kind": "Answers Robin Linus · BitVM bridges",
        "title": "Spend A only if B is co-spent",
        "date": "2026-04-28",
        "description": "A tapscript construction that binds a spend to a specific second UTXO through sha_prevouts, using only OP_CAT and OP_CHECKSIGFROMSTACK, confirmed on Bitcoin Inquisition signet.",
        "lede": "A tapscript construction that binds a spend to a specific second UTXO through <code>sha_prevouts</code>, using only OP_CAT and OP_CHECKSIGFROMSTACK. One signature passes both CSFS and CHECKSIG, so the script can read the real transaction.",
        "about": ["bitcoin", "taproot", "script", "schnorr"],
        "keywords": ["BitVM", "bridge connector", "sha_prevouts", "OP_CAT", "BIP 347", "OP_CHECKSIGFROMSTACK", "BIP 348", "covenant", "sighash preimage"],
        "question": [
            "Robin Linus's thread <em>How CTV+CSFS improves BitVM bridges</em> needs a connector: an operator's step must consume one specific UTXO. CTV commits to a transaction's outputs, not its inputs, and ajtowns showed that the scriptSig-based workaround is open to substitution.",
            "Can tapscript itself demand that a particular outpoint is spent in the same transaction?",
        ],
        "built": [
            "<strong>Same-signature binding.</strong> One Schnorr signature must pass OP_CHECKSIGFROMSTACK over a message the witness supplies and OP_CHECKSIG over the sighash the node computes. One signature cannot stand for two messages, so the witness copy of the sighash preimage has to be the real one.",
            "<strong>Preimage decomposition.</strong> The witness supplies the 212-byte preimage in chunks; the script inspects one chunk, then rebuilds the whole with OP_CAT.",
            "A 196-byte leaf that hardcodes B's outpoint. The witness supplies A's outpoint, and <code>SHA256(A || B)</code> must equal <code>sha_prevouts</code> at preimage bytes 10–41.",
            "Two confirmed spends of A with B. Swapping in a different coin C is rejected by <code>testmempoolaccept</code>: <em>Script failed an OP_EQUALVERIFY operation</em>.",
        ],
        "how": "witness (bottom -> top): sig(64) post_c(56) post_b(57) post_a(57) pre(10) sha(32) a_outpoint(36)\n\n<B_outpoint> CAT SHA256 SWAP DUP ROT EQUALVERIFY   # sha == SHA256(a_outpoint || B)\nSWAP SIZE 10 EQUALVERIFY                            # pre is 10 bytes -> sha sits at offset 10\nSWAP CAT SWAP CAT SWAP CAT SWAP CAT                 # pre||sha||post_a||post_b||post_c\n<tag[0:32]> <tag[32:64]> CAT SWAP CAT SHA256        # TapSighash(preimage)\nOVER SWAP <pk> CHECKSIGFROMSTACK VERIFY             # sig valid over witness preimage\n<pk> CHECKSIG                                       # same sig valid over real sighash",
        "how_note": "If C replaces B, the real <code>sha_prevouts</code> is <code>SHA256(A || C)</code>. Supplying it fails the EQUALVERIFY; supplying <code>SHA256(A || B)</code> makes the witness preimage differ from the real one, so the same signature cannot pass both checks.",
        "txs": [
            tx("Spend A + B", "b7959a71b74b8bbed69d52c22a9b3b90af176391be2d0b7f33eb1a6473304606", 300156),
            tx("Spend A + B (second round)", "7311da6e30886fab6594b633bcb97e4436d49f02ecc244d4bc7c59cb1ea83558", 300156),
        ],
        "rejected": "A + C (C substituted for B): rejected by testmempoolaccept, never broadcast.",
        "repo": "sighash-prevout-binding",
        "verify": {"command": "python3 verify_onchain.py", "result": "30/30 checks passed", "needs": "no keys, no node"},
        "not_shown": [
            "A signet experiment, not a bridge implementation.",
            "Assumes SIGHASH_DEFAULT, no annex and a script-path spend (the fixed 212-byte preimage layout).",
            "Same-signature binding needs a participating signer; keyless covenants are out of scope.",
        ],
        "sources": [
            ("Delving Bitcoin · How CTV+CSFS improves BitVM bridges, the question (#28)", "https://delvingbitcoin.org/t/how-ctv-csfs-improves-bitvm-bridges/1591/28"),
            ("Delving Bitcoin · the same thread, on-chain evidence (#29)", "https://delvingbitcoin.org/t/how-ctv-csfs-improves-bitvm-bridges/1591/29"),
            ("Delving Bitcoin · Taproot-native prevout binding via sighash preimage decomposition", "https://delvingbitcoin.org/t/taproot-native-prevout-binding-via-sighash-preimage-decomposition/2483"),
        ],
        "post": "https://delvingbitcoin.org/t/how-ctv-csfs-improves-bitvm-bridges/1591/29",
        "onchain": 2,
    },
    {
        "slug": "experiments/csfs-rekey-ladder",
        "kind": "Builds on Jeremy Rubin · CSFS rekey ladder",
        "title": "Rekey ladder theory",
        "date": "2026-04-20",
        "description": "An implementation of Jeremy Rubin and Rearden's CSFS rekey ladder, attacked in four stages, plus a three-round eltoo state chain settled in two transactions with only CSFS and CTV.",
        "lede": "An implementation of Jeremy Rubin and Rearden's CSFS rekey ladder, attacked in four stages to find where joint state binding holds and the exact condition that breaks it. Then the ladder on chain: a three-round eltoo state chain in two transactions, with only CSFS and CTV.",
        "about": ["bitcoin", "taproot", "script", "schnorr"],
        "keywords": ["rekey", "key ladder", "OP_CHECKSIGFROMSTACK", "BIP 348", "OP_CHECKTEMPLATEVERIFY", "LN-Symmetry", "eltoo", "state binding"],
        "question": [
            "In December 2024 Jeremy Rubin and Rearden described how CSFS plus CTV could support LN-Symmetry through re-keying and laddering: a root key hands authority to per-state keys, and each hop signs the next.",
            "CSFS only answers whether a signature is valid for a message and a key. Does a construction built from several such checks actually bind a whole state package, or can valid pieces from different states be recombined?",
        ],
        "built": [
            "<strong>E1</strong>, two independent CSFS checks: mixed packages from different states still pass. Pairwise validity is not joint binding.",
            "<strong>E2</strong>, a unique rekey per state: recombination fails, and comes back as soon as a rekey is reused.",
            "<strong>E3</strong>, a minimal key ladder: authorization holds hop by hop, and role confusion appears if the role gate is removed.",
            "<strong>E4</strong>, state-indexed key derivation: <code>key_n</code> verifies only <code>state_n</code>, unless the derivation leaves out the state index.",
            "On chain, a 42-byte tapscript of four CSFS checks and one CTV carries a three-hop ladder and settles a three-round state chain in two transactions.",
        ],
        "how": "<K_pub> CSFS VERIFY  CSFS VERIFY  CSFS VERIFY  CSFS VERIFY  CTV      # 42-byte leaf\n\nK    signs R_0's pubkey          # rekey: the root hands authority to state 0\nR_0  signs R_1's pubkey          # ladder hop\nR_1  signs R_2's pubkey          # ladder hop\nR_2  signs the CTV template hash # the final state is tied to its outputs\nCTV  enforces the 3-output payout",
        "how_note": "All delegation happens off chain; only the final spend goes on chain, carrying the whole ladder proof in a 12-element, 512-byte witness.",
        "txs": [
            tx("Fund the ladder + CTV output (101,000 sats)", "92efc47554d25d74d9f567594d37375d8c8a1a2ea6bd1864600d5a49531fda34", 300000),
            tx("Settlement of state 2", "b96324da612950339f564fbc88fe1d5c5751070e57bf796d32ee7171238382de", 300000, "Alice 40,000 / Bob 35,000 / Carol 25,000"),
        ],
        "repo": "rekey-ladder-theory",
        "verify": {"command": "python3 code/e1_naive_non_binding.py   # E1 to E4", "result": "each stage prints its attack scenarios and pass/fail", "needs": "Python 3.10+ and secp256k1"},
        "not_shown": [
            "The four stages model the verification predicate; they are not a script-interpreter or consensus-level proof.",
            "No proof of adaptor-signature equivalence.",
            "No economic or security quantification for production Lightning deployments.",
        ],
        "sources": [
            ("Jeremy Rubin and Rearden · CSFS + CTV rekey and ladder for LN-Symmetry (December 2024)", "https://rubin.io/bitcoin/2024/12/02/csfs-ctv-rekey-symmetry/"),
            ("Delving Bitcoin · Eltoo State Chain on Signet Again: Three Rounds, Two Transactions (CSFS + CTV)", "https://delvingbitcoin.org/t/2430"),
            ("On-chain ladder code · btcaaron examples/eltoo", "https://github.com/aaron-recompile/btcaaron/tree/main/examples/eltoo"),
        ],
        "post": "https://delvingbitcoin.org/t/2430",
        "onchain": 2,
    },
    {
        "slug": "experiments/braidpool-rca",
        "kind": "Answers Bob McElrath · Braidpool",
        "title": "Rolling coinbase aggregation",
        "date": "2026-04-15",
        "description": "An on-chain answer to Bob McElrath's covenant challenge for Braidpool: each new coinbase joins the pool through a two-input APO update, and only the latest CTV payout can settle.",
        "lede": "An answer, on chain, to Bob McElrath's covenant challenge for Braidpool: each new coinbase joins the pool through a two-input APO update, and only the latest CTV payout can settle.",
        "about": ["bitcoin", "taproot", "script"],
        "keywords": ["Braidpool", "mining pool", "rolling coinbase aggregation", "UHPO", "SIGHASH_ANYPREVOUT", "BIP 118", "OP_CHECKTEMPLATEVERIFY", "eltoo"],
        "question": [
            "Braidpool, a decentralized mining pool, has to hold coinbase rewards across many blocks before paying miners. Bob McElrath proposed a FROST federation that signs two chained transactions: the Rolling Coinbase Aggregation (RCA), which folds each new coinbase into the pool, and the Unspent Hasher Payout Object (UHPO), which pays everyone in proportion to work.",
            "He then asked covenant proposers for an alternative that removes custody, so that only the correct payouts can happen.",
        ],
        "built": [
            "Each RCA state is a three-leaf Taproot tree: a CTV leaf locked to this period's payout, an APO leaf for the next state, and a CSV timeout for solo recovery.",
            "Each round is a two-input transaction: the previous RCA spent through its APO leaf (sighash <code>0x41</code>), plus the new coinbase spent through its key path.",
            "The pool grows 32,750 → 63,500 → 92,750 sats while the payout split moves from A 100% to A 50 / B 50 to A 45 / B 35 / C 20.",
            "When an RCA is replaced, its payout leaf loses its only input, so only the latest UHPO can settle: 40,387 / 31,412 / 17,951 sats.",
        ],
        "how": "RCA vN  (P2TR, three leaves)\n  ctv_uhpo     <template_hash> OP_CHECKTEMPLATEVERIFY    # this period's payout\n  apo_update   <0x01 || xonly_pubkey> OP_CHECKSIG         # next RCA replaces this one\n  csv_escape   <2> OP_CSV OP_DROP <pk> OP_CHECKSIG        # timeout fallback\n\naggregation round:\n  input 0  RCA v(N-1)     script path, APO signature (0x41)\n  input 1  new coinbase   key path\n  output   RCA vN = sum of inputs - fee",
        "how_note": "APO handles the input side (the next state can be signed without the previous txid); CTV handles the output side (each RCA commits to the current payout). Dynamic payouts come from a sequence of static commitments.",
        "txs": [
            tx("Block #1 coinbase → RCA v1", "7557c229f29771410307055fabf907e4263899c140ff1963a81868c2ea7f5f7c", 299894, "32,750 sats"),
            tx("Block #2 coinbase", "600b9c7f990ce09b7bfc06406d9f9e8d75696f44b86069974abb81b5dc5bf063", 299894, "33,750 sats"),
            tx("Aggregation round 2 → RCA v2", "094a8aa1d572ac76d5f012ce6cb31f9cb9f4e982e9e90604e96b551c07d5ea9f", 299894, "pool 63,500 sats"),
            tx("Block #3 coinbase", "1bac796632961eb18f8e50db0b643862cf7c8f6923fe27068a29b760a3e1ea0c", 299894, "32,250 sats"),
            tx("Aggregation round 3 → RCA v3", "01a00ecba14dac6e60181f925bf2612dc9061d5791196a03270ccacfb4193206", 299894, "pool 92,750 sats"),
            tx("CTV settlement of v3", "7669e2519776a6af8ac3317ba64324282d3c14188256c0ef64dac5500800de5a", 299894, "40,387 / 31,412 / 17,951 sats"),
        ],
        "repo": "braidpool-rca-covenant",
        "verify": {"command": "python3 verify_onchain.py", "result": "61/61 checks passed", "needs": "no keys, no node"},
        "not_shown": [
            "No FROST federation, share accounting or Braidpool DAG.",
            "One demo key signs everything; the coinbases are wallet-funded stand-ins without coinbase maturity.",
            "The CSV leaf is committed but not spent; signing is sequential.",
            "Signet scale: 10,000 sats stand for 1 BTC.",
        ],
        "sources": [
            ("Delving Bitcoin · Challenge: Covenants for Braidpool (Bob McElrath)", "https://delvingbitcoin.org/t/challenge-covenants-for-braidpool/1370"),
            ("Delving Bitcoin · reply #2: the RCA tree, APO rebinding and the state chain", "https://delvingbitcoin.org/t/challenge-covenants-for-braidpool/1370/2"),
            ("Delving Bitcoin · reply #4: dynamic coinbase aggregation with growing amounts", "https://delvingbitcoin.org/t/challenge-covenants-for-braidpool/1370/4"),
        ],
        "post": "https://delvingbitcoin.org/t/challenge-covenants-for-braidpool/1370/2",
        "onchain": 6,
    },
]

PAPER = {
    "slug": "research/csfs-cat-covenant",
    "card_href": "https://delvingbitcoin.org/t/2659",
    "kind": "Paper · June 2026",
    "title": "Is CSFS+CAT already a general covenant primitive?",
    "full_title": "Capability Parity of CSFS+CAT with CTV and ANYPREVOUT for Common Covenant Patterns: On-Chain Evidence from Inquisition Signet",
    "date": "2026-06-25",
    "pages": 29,
    "ssrn": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7003839",
    "delving": "https://delvingbitcoin.org/t/2659",
    "repro": "https://github.com/aaron-recompile/btcaaron/tree/main/examples/csfs_cat_covenant_parity",
    "description": "With confirmed transactions on Bitcoin Inquisition signet, OP_CHECKSIGFROMSTACK plus OP_CAT reproduces the covenant capabilities of CTV and ANYPREVOUT for output binding, input binding and eltoo-style state replacement, for signer-participating spends.",
    "abstract": [
        "We show, with confirmed on-chain transactions on Bitcoin Inquisition signet, that the combination of OP_CHECKSIGFROMSTACK (BIP 348) and OP_CAT (BIP 347) reproduces the covenant capabilities of OP_CHECKTEMPLATEVERIFY (BIP 119) and BIP 118 ANYPREVOUT for three common patterns: output binding and input binding, built directly from CSFS+CAT, and the eltoo state-replacement pattern, realized through a CSFS delegation ladder with CTV settlement. The claim covers spends where the spending signer participates.",
        "The approach rests on two techniques. <strong>Same-signature binding</strong>: one Schnorr signature must satisfy both OP_CHECKSIG against the node-computed sighash and OP_CHECKSIGFROMSTACK against a witness-provided preimage, which forces the witness preimage to be byte-identical to the real one. <strong>Preimage decomposition</strong>: OP_CAT, OP_SIZE and witness padding emulate the disabled OP_SUBSTR, so Script can extract and verify any field of the preimage. Together they recover <code>sha_outputs</code>, <code>sha_prevouts</code> and <code>sha_amounts</code>.",
    ],
    "keywords": ["Bitcoin covenants", "OP_CAT", "OP_CHECKSIGFROMSTACK", "Tapscript", "sighash preimage introspection", "OP_CHECKTEMPLATEVERIFY", "ANYPREVOUT", "eltoo", "Bitcoin Inquisition signet"],
    "demos": [
        ("Output binding", "the same output template as CTV: <code>sha_outputs</code> forced to a hardcoded value", "2f345180bc6654353a247a50559c0be42153707b2ca29b621e57671ed41f37e6", 300379, "https://delvingbitcoin.org/t/taproot-native-prevout-binding-via-sighash-preimage-decomposition/2483/3"),
        ("Input binding", "beyond CTV's template: spend A only if B is co-spent", "7311da6e30886fab6594b633bcb97e4436d49f02ecc244d4bc7c59cb1ea83558", 300156, "/experiments/prevout-binding/"),
        ("Eltoo state replacement", "APO's use case through a CSFS + CTV delegation ladder: O(n) delegation, not O(1) rebinding", "b96324da612950339f564fbc88fe1d5c5751070e57bf796d32ee7171238382de", 300000, "/experiments/csfs-rekey-ladder/"),
    ],
    "not_claimed": [
        "Capability, not efficiency: these scripts and witnesses are larger, and the dedicated opcodes are far cheaper.",
        "Signer-participating spends only; keyless covenants are out of scope.",
        "Not an argument that CAT is harmless, and no position for or against activating any opcode.",
    ],
}

NAV = '<nav><div class="wrap"><a class="site" href="/">bitcoincoding.dev</a><ul><li><a href="/#books">Books</a></li><li><a href="/#research">Research</a></li><li><a href="/#experiments">Experiments</a></li><li><a href="/#writing">Writing</a></li><li><a href="/#tools">Tools</a></li><li><a href="/#about">About</a></li></ul></div></nav>'
FOOTER = '<footer><span>© Aaron Zhang · <a href="/">bitcoincoding.dev</a></span><a href="https://github.com/aaron-recompile">github.com/aaron-recompile</a></footer>'
PERSON_REF = {"@type": "Person", "@id": PERSON_ID, "name": "Aaron Zhang", "alternateName": "Aaron Recompile", "url": f"{SITE}/#about"}


def esc(s):
    return html.escape(s, quote=True)


def plain(s):
    """Strip inline HTML for machine fields."""
    return html.unescape(re.sub(r"<[^>]+>", "", s))


def glyph_for(href, index_html):
    """The glyph of the homepage card whose title links to href."""
    m = re.search(r'<div class="head"><div class="kind">[^<]*</div>(<svg class="glyph"(?:(?!</svg>).)*</svg>)</div>\s*<h3><a href="' + re.escape(href) + '"', index_html, re.S)
    return m.group(1).replace('class="glyph"', 'class="big-glyph"') if m else ""


def short(txid):
    return f"{txid[:8]}…{txid[-4:]}"


def tx_table(rows):
    out = ['<div class="tablewrap"><table><thead><tr><th>Step</th><th>Transaction</th><th>Block</th><th>Note</th></tr></thead><tbody>']
    for r in rows:
        out.append(f'<tr><td>{esc(r["role"])}</td><td class="mono"><a href="{MEMPOOL}{r["txid"]}">{short(r["txid"])}</a></td><td class="mono">{r["block"] or ""}</td><td>{esc(r["note"])}</td></tr>')
    out.append("</tbody></table></div>")
    return "".join(out)


def head(title, description, canonical, jsonld, extra=""):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · bitcoincoding.dev</title>
<meta name="description" content="{esc(description)}">
<meta name="author" content="Aaron Zhang">
<link rel="canonical" href="{canonical}">
<link rel="alternate" type="application/json" href="facts.json" title="Machine-readable facts for this page">
<meta property="og:type" content="article">
<meta property="og:site_name" content="bitcoincoding.dev">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE}/assets/og.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@aaron_recompile">
{extra}<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<script data-goatcounter="https://bitcoincoding.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
<link rel="stylesheet" href="/assets/page.css">
<script type="application/ld+json">
{json.dumps(jsonld, ensure_ascii=False, indent=1)}
</script>
</head>
<body>
{NAV}
<main class="wrap">
"""


def record_block(facts):
    return f'<details class="record"><summary>Technical record · facts.json</summary><pre><code>{esc(json.dumps(facts, ensure_ascii=False, indent=2))}</code></pre></details>'


def all_txs(e):
    if "parts" not in e:
        return e["txs"]
    return [dict(t, part=p["label"]) for p in e["parts"] for t in p["txs"]]


def render_parts(e):
    out = []
    for p in e["parts"]:
        out.append(f'<section><h2>{esc(p["label"])}</h2><h3 class="part">{esc(p["title"])}</h3>')
        out += [f"<p>{x}</p>" for x in p.get("paras", [])]
        if p.get("table"):
            head_row, rows = p["table"]
            out.append('<div class="tablewrap"><table><thead><tr>' + "".join(f"<th>{esc(h)}</th>" for h in head_row) + "</tr></thead><tbody>"
                       + "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows) + "</tbody></table></div>")
        if p.get("how"):
            out.append(f'<pre><code>{esc(p["how"])}</code></pre>')
        if p.get("proof_title"):
            out.append(f'<h3 class="part small">{esc(p["proof_title"])}</h3><p>{p["proof"]}</p>')
        out.append(tx_table(p["txs"]))
        if p.get("after"):
            out.append(f'<p class="callout">{p["after"]}</p>')
        out.append("</section>")
    return "".join(out)


def build_experiment(e, index_html):
    url = f"{SITE}/{e['slug']}/"
    repo = GH + e["repo"]
    facts = {
        "page": url,
        "title": e["title"],
        "context": e["kind"],
        "author": "Aaron Zhang (Aaron Recompile)",
        "date": e["date"],
        "network": "Bitcoin Inquisition signet",
        "summary": plain(e["lede"]),
        "transactions": [{"role": t["role"], "txid": t["txid"], "block": t["block"], "explorer": MEMPOOL + t["txid"], **({"note": t["note"]} if t["note"] else {}), **({"part": t["part"]} if t.get("part") else {})} for t in all_txs(e)],
        "verify": {"repository": repo, **e["verify"]},
        "does_not_show": e["not_shown"],
        "sources": [{"title": t, "url": u} for t, u in e["sources"]],
    }
    if e.get("discussion"):
        facts["discussion"] = [{"title": t, "url": u} for t, u in e["discussion"]]
    if e.get("code_links"):
        facts["code"] = [{"title": t, "url": u} for t, u in e["code_links"]]
    if e.get("rejected"):
        facts["negative_test"] = e["rejected"]
    jsonld = {"@context": "https://schema.org", "@graph": [
        {"@type": "TechArticle", "@id": url + "#article", "headline": e["title"], "description": e["description"],
         "url": url, "datePublished": e["date"], "inLanguage": "en", "author": PERSON_REF, "publisher": {"@id": f"{SITE}/#site"},
         "about": [THING[a] for a in e["about"]], "keywords": ", ".join(e["keywords"]),
         "isBasedOn": [u for _, u in e["sources"]] + [u for _, u in e.get("discussion", [])], "hasPart": {"@id": url + "#code"}, "mainEntityOfPage": url},
        {"@type": "SoftwareSourceCode", "@id": url + "#code", "name": e["repo"], "codeRepository": repo,
         "programmingLanguage": "Python", "license": "https://opensource.org/licenses/MIT", "author": {"@id": PERSON_ID}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "bitcoincoding.dev", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Experiments", "item": SITE + "/#experiments"},
            {"@type": "ListItem", "position": 3, "name": e["title"], "item": url}]},
    ]}
    chips = [f'<span class="chip">{e["date"][:7].replace("-", " · ")}</span>', '<span class="chip">Inquisition signet</span>']
    if e.get("onchain"):
        chips.append(f'<span class="chip ok">✓ {e["onchain"]} tx confirmed</span>')
    if "checks" in e["verify"]["result"]:
        chips.append(f'<span class="chip ok">{esc(e["verify"]["result"])}</span>')
    body = [head(e["title"], e["description"], url, jsonld),
            '<p class="crumb"><a href="/">bitcoincoding.dev</a> / <a href="/#experiments">Experiments</a></p>',
            f'<header class="top"><div><div class="kind">{esc(e["kind"])}</div><h1>{esc(e["title"])}</h1>',
            f'<p class="lede">{e["lede"]}</p><div class="facts">{"".join(chips)}</div>',
            f'<div class="actions"><a class="btn primary" href="{repo}">{ICON_GH}Code</a><a class="btn" href="{e["post"]}">{ICON_TALK}Delving Bitcoin</a></div></div>',
            glyph_for(f"/{e['slug']}/", index_html), '</header>',
            '<section><h2>The question</h2>' + "".join(f"<p>{p}</p>" for p in e["question"]) + '</section>',
            render_parts(e) if "parts" in e else (
            '<section><h2>What was built</h2><ul class="points">' + "".join(f"<li>{b}</li>" for b in e["built"]) + '</ul></section>'
            + f'<section><h2>How it works</h2><pre><code>{esc(e["how"])}</code></pre><p class="callout">{e["how_note"]}</p></section>'
            + '<section><h2>On chain</h2>' + tx_table(e["txs"]) + (f'<p class="callout">{esc(e["rejected"])}</p>' if e.get("rejected") else "") + '</section>'),
            f'<section><h2>Check it yourself</h2><p>The repository re-checks every claim on this page ({esc(e["verify"]["needs"])}).</p>'
            f'<pre class="term"><code>git clone {repo}\ncd {e["repo"]}\n{esc(e["verify"]["command"])}\n<span class="ok">{esc(e["verify"]["result"])}</span></code></pre>'
            + ('<ul class="points sources">' + "".join(f'<li><a href="{u}">{esc(t)}</a></li>' for t, u in e["code_links"]) + '</ul>' if e.get("code_links") else "") + '</section>',
            '<section><h2>What it does not show</h2><ul class="points">' + "".join(f"<li>{esc(x)}</li>" for x in e["not_shown"]) + '</ul></section>',
            ('<section class="sources"><h2>Discussion</h2><ul class="points">' + "".join(f'<li><a href="{u}">{esc(t)}</a></li>' for t, u in e["discussion"]) + '</ul></section>' if e.get("discussion") else ""),
            '<section class="sources"><h2>Sources</h2><ul class="points">' + "".join(f'<li><a href="{u}">{esc(t)}</a></li>' for t, u in e["sources"]) + '</ul></section>',
            record_block(facts), FOOTER, '</main>\n</body>\n</html>\n']
    write_page(e["slug"], "\n".join(body), facts)


def build_paper(p):
    url = f"{SITE}/{p['slug']}/"
    pdf = url + "paper.pdf"
    facts = {
        "page": url, "title": p["full_title"], "short_title": p["title"], "author": "Aaron Zhang (Aaron Recompile)",
        "orcid": "https://orcid.org/0009-0001-1599-092X", "date": p["date"], "pages": p["pages"], "pdf": pdf,
        "ssrn": p["ssrn"], "discussion": p["delving"], "reproduction": p["repro"], "keywords": p["keywords"],
        "abstract": [plain(a) for a in p["abstract"]],
        "on_chain_demonstrations": [{"pattern": n, "what": plain(w), "txid": t, "block": b, "explorer": MEMPOOL + t} for n, w, t, b, _ in p["demos"]],
        "does_not_claim": p["not_claimed"],
    }
    jsonld = {"@context": "https://schema.org", "@graph": [
        {"@type": "ScholarlyArticle", "@id": url + "#paper", "headline": p["full_title"], "alternativeHeadline": p["title"],
         "name": p["full_title"], "abstract": " ".join(plain(a) for a in p["abstract"]), "description": p["description"],
         "url": url, "datePublished": p["date"], "inLanguage": "en", "numberOfPages": p["pages"],
         "author": {**PERSON_REF, "sameAs": ["https://orcid.org/0009-0001-1599-092X"]},
         "keywords": ", ".join(p["keywords"]), "about": [THING["bitcoin"], THING["taproot"], THING["script"], THING["schnorr"]],
         "encoding": {"@type": "MediaObject", "contentUrl": pdf, "encodingFormat": "application/pdf"},
         "sameAs": [p["ssrn"]], "discussionUrl": p["delving"], "isAccessibleForFree": True},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "bitcoincoding.dev", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Research", "item": SITE + "/#research"},
            {"@type": "ListItem", "position": 3, "name": p["title"], "item": url}]},
    ]}
    # Highwire Press tags: what Google Scholar reads.
    scholar = "".join(f'<meta name="{k}" content="{esc(v)}">\n' for k, v in [
        ("citation_title", p["full_title"]), ("citation_author", "Zhang, Aaron"),
        ("citation_publication_date", p["date"].replace("-", "/")), ("citation_pdf_url", pdf),
        ("citation_abstract_html_url", url), ("citation_language", "en"),
        ("citation_keywords", "; ".join(p["keywords"])), ("citation_technical_report_institution", "SSRN"),
        ("citation_technical_report_number", "7003839")])
    bibtex = ("@misc{zhang2026capability,\n  author = {Zhang, Aaron},\n  title  = {" + p["full_title"] + "},\n"
              "  year   = {2026},\n  month  = jun,\n  note   = {SSRN 7003839},\n  url    = {" + url + "}\n}")
    demo_rows = "".join(
        f'<tr><td><strong>{esc(n)}</strong><br><span style="color:var(--muted)">{w}</span></td><td class="mono"><a href="{MEMPOOL}{t}">{short(t)}</a></td><td class="mono">{b}</td><td><a href="{link}">{"Experiment page" if link.startswith("/") else "Write-up"}</a></td></tr>'
        for n, w, t, b, link in p["demos"])
    body = [head(p["title"], p["description"], url, jsonld, scholar),
            '<p class="crumb"><a href="/">bitcoincoding.dev</a> / <a href="/#research">Research</a></p>',
            f'<header class="top"><div><div class="kind">{esc(p["kind"])}</div><h1>{esc(p["title"])}</h1>',
            f'<p class="subtitle">{esc(p["full_title"])}</p>',
            f'<p class="lede">{esc(p["description"])}</p>',
            f'<div class="facts"><span class="chip">Aaron Zhang</span><span class="chip">{p["pages"]} pages</span><span class="chip ok">✓ 3 on-chain demonstrations</span></div>',
            f'<div class="actions"><a class="btn primary" href="paper.pdf">{ICON_DOC}Read the PDF</a><a class="btn" href="{p["ssrn"]}">SSRN</a><a class="btn" href="{p["delving"]}">{ICON_TALK}Delving Bitcoin</a></div></div></header>',
            '<section><h2>Abstract</h2>' + "".join(f"<p>{a}</p>" for a in p["abstract"]) + '</section>',
            '<section><h2>Three on-chain demonstrations</h2><div class="tablewrap"><table><thead><tr><th>Pattern</th><th>Transaction</th><th>Block</th><th></th></tr></thead><tbody>' + demo_rows + '</tbody></table></div></section>',
            '<section><h2>What the paper does not claim</h2><ul class="points">' + "".join(f"<li>{esc(x)}</li>" for x in p["not_claimed"]) + '</ul></section>',
            f'<section><h2>Reproduce</h2><p>Every construction can be checked from its confirmed witness on a block explorer; no private keys are needed. The reproduction package lives in <a href="{p["repro"]}">btcaaron</a>.</p></section>',
            f'<section><h2>Cite</h2><pre><code>{esc(bibtex)}</code></pre></section>',
            record_block(facts), FOOTER, '</main>\n</body>\n</html>\n']
    write_page(p["slug"], "\n".join(body), facts)


def write_page(slug, page_html, facts):
    d = ROOT / slug
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(page_html)
    (d / "facts.json").write_text(json.dumps(facts, ensure_ascii=False, indent=2) + "\n")


TAPROOT_CHAPTERS = [
    "Chapter_01_Private_Keys", "Chapter_02_Bitcoin_Script_Fundamentals", "Chapter_03_P2SH_Script_Engineering",
    "Chapter_04_Building_SegWit_Transactions", "Chapter_05_Taproot_The_Evolution", "Chapter_06_Building_Real_Taproot_Contracts",
    "Chapter_07_Taproot_Dual_Leaf_Script_Tree", "Chapter_08_Four_Leaf_Taproot_Script_Tree"]


def build_sitemap():
    urls = [SITE + "/"] + [f"{SITE}/{x['slug']}/" for x in [PAPER] + EXPERIMENTS]
    urls += [f"{SITE}/mastering-taproot-interactive/", f"{SITE}/bitcoin-from-scratch-interactive/"]
    urls += [f"{SITE}/mastering-taproot-interactive/notebooks/en/{c}.html" for c in TAPROOT_CHAPTERS]
    body = "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls)
    (ROOT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}</urlset>\n')


def build_llms():
    lines = [
        "# bitcoincoding.dev",
        "",
        "> Learn Bitcoin by building it. Books, explainers, research and experiments by Aaron Zhang (Aaron Recompile), Bitcoin developer, educator and investor. Every idea comes as code you can run.",
        "",
        "Author: Aaron Zhang, also known as Aaron Recompile (GitHub: aaron-recompile). Author of Mastering Taproot and Bitcoin from Scratch.",
        "",
        "## Books",
        f"- [Bitcoin from Scratch]({SITE}/bitcoin-from-scratch-interactive/): build your own Bitcoin chain from a single byte to a working network, Python standard library only; every code cell runs in the browser. 18 chapters, beginner to intermediate.",
        f"- [Mastering Taproot]({SITE}/mastering-taproot-interactive/): Taproot script engineering for developers: keys and addresses, P2SH, SegWit, Taproot contracts and script trees, verified on testnet. 8 chapters.",
        "",
        "## Booklets: Covenants from First Principles",
        "- [What a Signature Can See](https://sighash.bitcoincoding.dev/) (Volume I): sighash from the ground up, with a playground that shows which transaction fields a signature commits to.",
        "- [The Grammar of Extensibility](https://slots.bitcoincoding.dev/) (Volume II): Bitcoin's reserved upgrade slots at the byte level and which one CAT, CSFS, CTV and APO plug into.",
        "",
        "## Research",
        f"- [{PAPER['full_title']}]({SITE}/{PAPER['slug']}/): {PAPER['description']} PDF: {SITE}/{PAPER['slug']}/paper.pdf",
        "",
        "## Experiments (open problems posed by other builders, answered in code)",
    ]
    lines += [f"- [{e['title']}]({SITE}/{e['slug']}/) ({e['kind']}): {e['description']} Code: {GH}{e['repo']}" for e in EXPERIMENTS]
    lines += [
        "",
        "## Writing",
        "- [Recompile Archive](https://archive.bitcoincoding.dev/): technical articles on Taproot, Script and covenant opcodes on signet, grouped into series.",
        "",
        "## Tools",
        "- [btcaaron](https://github.com/aaron-recompile/btcaaron): Python Taproot toolkit with templates for Bitcoin Inquisition opcodes.",
        "- [RootScope](https://github.com/aaron-recompile/rootscope): Taproot script-path analyzer.",
        "- [btcrun](https://github.com/aaron-recompile/btcrun): Bitcoin chain manager and regtest dev tool.",
        "",
        "## Machine-readable",
        "- Each research and experiment page has a facts.json next to it with transactions, verification commands and sources.",
        f"- Sitemap: {SITE}/sitemap.xml",
        "",
    ]
    (ROOT / "llms.txt").write_text("\n".join(lines))


if __name__ == "__main__":
    index_html = (ROOT / "index.html").read_text()
    for e in EXPERIMENTS:
        build_experiment(e, index_html)
    build_paper(PAPER)
    build_sitemap()
    build_llms()
    print("built", len(EXPERIMENTS) + 1, "pages, sitemap.xml, llms.txt")
