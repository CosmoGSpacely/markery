# Research Framework

## The Central Argument

The history of information technology in America has a blind spot: the fifty years before the computer. Between roughly 1880 and 1940, American businesses built extraordinarily sophisticated systems for managing information at scale — personnel records, inventory, accounts receivable, correspondence, customer indexes — using entirely non-electronic means. These systems were engineered, manufactured, patented, trademarked, and sold by major industrial companies. They were adopted by corporations, insurance companies, railroads, governments, and hospitals across the country. And they are almost entirely absent from the standard history of information technology, which tends to begin its serious account with ENIAC, or at the earliest with Hollerith's 1890 census tabulator as a precursor to IBM.

This project argues that the combined USPTO trademark and patent record is one of the richest available primary sources for recovering that history — and that reading the two records together reveals things that neither shows alone.

---

## The Two Records and Why They Need Each Other

The **trademark record** establishes the commercial surface of a technology: what a company called its product, when it entered commerce, what goods it was sold alongside, and how the company wanted to be seen by its customers. A trademark filing is a company declaring its identity to the public record. When Rand Kardex Bureau filed SOUNDEX in March 1927, they were announcing that the Russell phonetic indexing algorithm — which had existed as a patent for nine years — was now a branded commercial product with a name, a visual identity, and a market position.

The **patent record** establishes the technical substance: what was invented, who invented it, who owned the invention, and when it was considered commercially significant enough to protect. When Robert C. Russell assigned his 1918 patent for phonetic name-indexing to the Remington Typewriter Company, the record captures not just the algorithm but the corporate structure that would bring it to market.

Neither record alone completes the picture. A patent without a trademark tells you that something was invented but not necessarily that it was sold — the patent record is full of inventions that never became products. A trademark without a patent tells you that something was sold under a name but not what was technically novel about it or who invented it. A confirmed patent-trademark pair tells you that an invention became a product, when that transition happened, who controlled it at each stage, and what they called it when they sold it.

---

## The Information Systems Focus

The immediate research project — `projects/information-systems/` — concentrates on the pre-computer information management industry: the companies that made filing cabinets, card-index systems, visible record equipment, loose-leaf binders, tabulating machines, and the phonetic and physical indexing systems that organized large record sets.

This focus is justified by the density of the material. The period 1900–1939 was the commercial peak of this industry. The CPC class B42F alone yields 7,000+ US patents in this window. Companies like Remington Rand, Wilson Jones, Yawman & Erbe, and Rand Kardex Bureau were filing dozens of patents per year alongside regular trademark registrations. The cross-reference between the two records is tractable at this scale and historically significant.

It is also justified by the stakes. The systems these companies built were not marginal. The Soundex algorithm, patented by Remington and commercialized by Rand Kardex, became the indexing system for the WPA's New Deal-era census index project — the primary mechanism by which Americans could prove their birth year to claim Social Security benefits. The Kardex visible record system was used by hospitals, retailers, and manufacturers across the country to manage operational data in real time. These were the information infrastructure of industrial America.

---

## What the Existing Literature Covers

The scholarly literature on pre-computer information systems is smaller than the subject deserves, but several works are indispensable:

**JoAnne Yates, *Control Through Communication: The Rise of System in American Management* (1989)** — the foundational account of how American corporations developed systematic internal communication practices between 1880 and 1920, covering the vertical file, the carbon copy, the form letter, and the typewriter as tools of managerial coordination. Yates is excellent on the organizational demand for information systems; less detailed on the specific manufacturers and their commercial strategies.

**JoAnne Yates, *Structuring the Information Age: Life Insurance and Technology in the Twentieth Century* (2005)** — a detailed study of how the life insurance industry adopted punched card tabulating systems from Hollerith through IBM. The best account of how one major industry sector integrated computational tools into its operations.

**James W. Cortada, *Before the Computer: IBM, NCR, Burroughs, and Remington Rand and the Industry They Created, 1865–1956* (1993)** — a business history of the major office machine manufacturers. Indispensable for corporate chronology and product lineages, though Cortada's focus is on the large machine companies (tabulators, cash registers) rather than the filing systems industry.

**Geoffrey Austrian, *Herman Hollerith: Forgotten Giant of Information Processing* (1982)** — the biography of the Hollerith tabulator and its development into what became IBM. The most detailed account of the punched card's commercial origins.

**Alfred D. Chandler Jr., *The Visible Hand: The Managerial Revolution in American Business* (1977)** — not specifically about information systems, but the analytical framework for understanding why large American corporations created demand for them. Chandler's account of the managerial revolution — the separation of ownership from operational control and the rise of professional managers coordinating multi-unit enterprises — explains what filing cabinets and card indexes were *for*.

---

## The Gap This Project Fills

None of these works systematically cross-references trademark records with patent records for this period and industry. Yates uses corporate histories and trade publications; Cortada uses company archives; Austrian uses patent records and corporate documents for Hollerith but not the broader trademark record. The combined trademark-patent cross-reference as a research method — identifying product-level correspondences between branded names and technical inventions — has not been applied to this industry.

The practical consequence is that the commercial history of specific products is difficult to recover. Who invented the overlapping visible card tray that became the Kardex system? When did that invention become a named product? What happened to the brand after the corporate mergers of the late 1920s? These questions have answers in the combined record that are not assembled anywhere in the existing literature.

This project assembles them, entry by entry, beginning with the information systems industry and the companies that defined it.

---

## Method: The Confirmed Pair

The unit of research output is the **confirmed patent-trademark pair**: a specific US patent and a specific USPTO trademark registration, for the same corporate entity, where the patent describes the technical basis of the named product.

Confirmed pairs are recorded in `projects/<project>/matches/confirmed.jsonl` and developed into research essays in `projects/<project>/content/`. The essay form follows a consistent structure: historical context, primary source evidence, interpretation. The evidence section always cites specific filing records — serial number, registration number, patent number, dates, goods descriptions — so the reader can verify the claim against the original sources.

Candidate pairs are generated algorithmically by the `match/` pipeline, scored by date proximity and product-class relevance, and reviewed by hand before confirmation. The algorithm surfaces candidates; human judgment confirms them. A high-scoring candidate where the trademark is a company name (REMINGTON, RAND) rather than a product name (KARDEX, VARIADEX, SOUNDEX) is noted but not confirmed as a product-level correspondence.
