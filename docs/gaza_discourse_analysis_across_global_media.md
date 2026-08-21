User:

Please refer to the attached documents. This research project involves data collection (news) from several Global North and Global South vehicles to conduct discourse analysis through Lexical Multidimensional Analysis. The news to be collected from online news vehicles may be subjected to anti-bot and paywall restrictions. Ideally, they should be ethically web scraped.

The period of interest is from 2023 to nowadays. The seed term is 'gaza'.

What do you think?

AI Assistant:

I think the project is **feasible and promising**, but the corpus design and data-collection protocol need to be tightened before scraping begins. The central challenge is not only technical — anti-bot systems, paywalls, dynamic pages — but also **methodological and ethical**: the corpus must be balanced, reproducible, legally defensible, and suitable for Lexical Multidimensional Analysis.

## 1. Overall assessment

The project has a clear research objective: compare **Global North and Global South news discourses** around Gaza/Palestine from 2023 to the present, using **Lexical Multidimensional Analysis**.

That is a strong design because:

- the topic is highly discursively polarized;
- there is enough news volume from 2023 onward;
- the contrast between Global North and Global South media is theoretically motivated;
- LMDA is appropriate for detecting latent lexical-discursive dimensions;
- the use of English-language news allows cross-source comparison, though with important limitations.

However, the project should avoid simply “collecting as much as possible.” For LMDA, what matters is not only size, but **comparability** across:

- source type;
- country/region;
- publication date;
- genre;
- article length;
- topic relevance;
- access method;
- duplication status;
- translation status;
- corpus section size.

## 2. Recommended corpus design

I would structure the corpus into two main sections:

| Section      | Sources                                                                                   | Collection mode                     |
|--------------|-------------------------------------------------------------------------------------------|-------------------------------------|
| Global North | US, UK, Canada, Australia, Israel                                                         | NOW Corpus + ethical web collection |
| Global South | China, Russia, Iran, Qatar, South Africa, Pakistan/Nigeria/Kenya if available through NOW | NOW Corpus + ethical web collection |

The current list of vehicles is usable, but it may need pruning. Some sources are easier and more ethically collectable than others.

### Suggested Global North sources

From the documents, likely candidates include:

- **United States**: *New York Times*, *Washington Post*
- **United Kingdom**: *The Guardian*, *The Times*, possibly *Daily Mail*
- **Israel**: *Haaretz*, *Jerusalem Post*, *Times of Israel*
- **Canada**: *The Globe and Mail*, *National Observer*
- **Australia**: *The Australian*, *Sydney Morning Herald*

But some of these have strong paywall restrictions. For example, *New York Times*, *Washington Post*, *The Times*, *Haaretz*, *The Australian*, and *The Globe and Mail* may be difficult to scrape ethically if the full text is behind a paywall.

### Suggested Global South sources

Good candidates include:

- **Qatar**: *Al Jazeera*
- **China**: *China Daily*, *People’s Daily Online*, *Global Times*
- **Russia**: *TASS*, *The Moscow Times*, *Meduza*
- **Iran**: *Tehran Times*, *Mehr News Agency*, *Iran Daily*
- **South Africa**: *News24*, *Daily Maverick*, *The South African*

Again, paywall and access conditions vary. *Al Jazeera*, *TASS*, *China Daily*, *People’s Daily*, *Global Times*, *Tehran Times*, and *Mehr News* are likely more accessible than many Global North newspapers.

## 3. Important methodological concern: “Global North” and “Global South” are not identical to “Western” and “non-Western”

The project should be careful with classification. Some examples are complicated:

- **Israel** is geographically in the Middle East but politically and institutionally often aligned with the Global North in this research framing.
- **Russia** is not always straightforwardly “Global South”; it may function as a non-Western or anti-Western geopolitical pole rather than a classic Global South case.
- **Qatar/Al Jazeera** is also complex: Qatar is wealthy, but Al Jazeera often circulates perspectives not dominant in US/UK media.
- **China** is economically powerful but often positioned as Global South or non-Western in geopolitical discourse.
- **South Africa** is a stronger Global South case.

So I would explicitly define the labels as **analytical categories**, not geographical facts. Perhaps use:

- **Global North / Western-aligned media**
- **Global South / non-Western or counter-hegemonic media**

Or retain “Global North” and “Global South” but add a paragraph explaining the classification logic.

## 4. Time period

The period “2023 to nowadays” should be operationalized more precisely.

I recommend:

> **1 January 2023 to the date of corpus closure**

But because the Gaza war escalated dramatically after **7 October 2023**, you may want subperiods:

| Period                | Rationale                                              |
|-----------------------|--------------------------------------------------------|
| Jan 2023 – 6 Oct 2023 | Pre-October baseline                                   |
| 7 Oct 2023 – Dec 2023 | Immediate war/crisis framing                           |
| 2024                  | Consolidation of discourses                            |
| 2025–corpus closure   | Later discourse, legal/diplomatic/humanitarian framing |

This would allow the LMDA analysis to compare not only North/South but also diachronic shifts.

## 5. Search term strategy

The seed term **“gaza”** is a good starting point, but it is too narrow if used alone.

I recommend using `"gaza"` as the primary mandatory seed for the first corpus, then possibly building an expanded corpus with related terms.

### Core query

Use:

```plain text
gaza
```


### Expanded query set

Possible additional terms:

```plain text
Gaza
Palestine
Palestinian
Israel
Israeli
Hamas
IDF
Rafah
Khan Younis
West Bank
ceasefire
hostages
genocide
humanitarian aid
occupation
settlements
two-state solution
UNRWA
```


But be careful: if the terms are too broad, the corpus may include many texts not actually centered on Gaza. A practical solution is:

- collect candidate texts with broader terms;
- retain only texts where **Gaza** appears in title, subtitle, tags, or above a minimum threshold in body text.

For example:

> Include article if `gaza` appears in the title, subtitle, metadata keywords, or at least twice in the body.

## 6. Ethical web scraping protocol

The ethical issue is central. I would recommend a conservative protocol:

### Do

- Prefer official APIs, RSS feeds, sitemaps, site search pages, and openly accessible HTML.
- Respect `robots.txt` where applicable.
- Respect each site’s Terms of Service.
- Use low request rates.
- Identify the project in the user agent when appropriate.
- Cache pages to avoid repeated requests.
- Collect only articles that are publicly accessible without login, payment, CAPTCHA circumvention, or technical bypass.
- Store bibliographic metadata and a URL for traceability.
- Store only what is needed for academic analysis.
- Document collection date, source, query, and access status.
- Avoid republishing full copyrighted texts.
- Use text internally for analysis and publish only derived statistics, short quotations, and metadata when allowed.

### Do not

- Circumvent paywalls.
- Bypass CAPTCHA or anti-bot mechanisms.
- Use stolen/session cookies.
- Simulate logged-in subscribers.
- Use residential proxy networks to evade rate limits.
- Hammer websites with high-volume requests.
- Redistribute full article texts without permission.
- Ignore explicit takedown or no-scraping policies.

A good guiding principle would be:

> If an article is not available to a normal public visitor without login, payment, or technical evasion, it should not be scraped directly.

## 7. How to handle paywalled sources

For paywalled sources, there are several ethical alternatives.

### Option 1: Use metadata only

For inaccessible articles, collect only:

- title;
- author;
- date;
- section;
- abstract/standfirst if publicly visible;
- URL;
- source;
- access status.

But these should not be mixed with full-text articles in LMDA.

### Option 2: Use licensed databases

If the institution has access, use:

- Factiva;
- LexisNexis;
- ProQuest Newsstream;
- Gale;
- Nexis Uni;
- institutional newspaper archives.

This is often the best route for NYT, Washington Post, The Times, etc.

### Option 3: Use NOW Corpus

Since the project already mentions NOW, it can reduce scraping burdens. NOW may provide consistent English-language news material for some countries and sources.

### Option 4: Replace heavily paywalled sources

For balance, it may be better to select sources that are openly accessible. For instance:

- Use *The Guardian* instead of *The Times* if access is easier.
- Use *Times of Israel* or *Jerusalem Post* cautiously if more accessible than *Haaretz*.
- Use *Al Jazeera*, *TASS*, *China Daily*, *People’s Daily*, *Global Times*, *Tehran Times*, and *Mehr News* where access is public.

The corpus should not be methodologically distorted by including mostly open Global South state media and mostly paywalled Global North elite media. That could create a genre/source-access bias.

## 8. Balance and sampling

For LMDA, I would strongly recommend a controlled sampling plan.

Possible target:

| Level               | Target                  |
|---------------------|-------------------------|
| Articles per source | 100–300                 |
| Sources per section | 6–10                    |
| Total per section   | 1,500–3,000 articles    |
| Time span           | Jan 2023–corpus closure |
| Article type        | News reports only       |

If volume is uneven, use stratified sampling:

- equal number of articles per source;
- equal or similar number per month or quarter;
- separate Global North and Global South sections;
- exclude duplicates and syndicated copies.

### Suggested metadata fields

Each article should have at least:

```plain text
article_id
source
country
global_section
url
title
subtitle
author
publication_date
collection_date
section/category
article_type
language
access_method
query_term
full_text_available
word_count
duplicate_group_id
copyright_status
notes
```


For LMDA, also later add:

```plain text
tokens
lemmas
pos_tags
content_lemmas
normalized_frequencies
keyness_scores
factor_scores
```


## 9. Genre control

This is very important. The documents say “news reporting,” but many websites mix:

- breaking news;
- opinion;
- analysis;
- editorials;
- live blogs;
- explainers;
- interviews;
- letters;
- wire-service republications;
- photo essays;
- video pages.

For LMDA, I would either:

### Option A: Include only news reports

This is cleaner.

Exclude:

- opinion;
- editorials;
- live updates;
- podcasts;
- videos;
- letters;
- photo galleries;
- duplicated wire reports.

### Option B: Include multiple genres but tag them

Then compare genre effects separately.

But for the first phase, I recommend **news reports only**.

## 10. Duplicates and syndicated texts

This topic will have many duplicate or near-duplicate texts, especially from agencies such as Reuters, AP, AFP, TASS, and state agencies.

You should detect:

- exact duplicate URLs;
- identical titles;
- identical article bodies;
- near duplicates using similarity measures;
- syndicated copies from wire agencies.

If duplicates are not controlled, LMDA may detect **syndication patterns** rather than discourse differences.

## 11. Translation and English-language bias

The project focuses on English-language sources. That is practical, but theoretically important.

Many Global South English texts are:

- translated from another language;
- written for international audiences;
- produced by state-facing international desks;
- stylistically shaped by English-language diplomatic or journalistic conventions.

This should be acknowledged as a limitation:

> The corpus does not represent domestic-language media discourse as a whole, but English-language international-facing news discourse.

This is not a fatal problem. It may actually become part of the research object: how different geopolitical actors address an international English-reading public.

## 12. Recommendation for source prioritization

I would divide sources into tiers.

### Tier 1: likely feasible/open sources

These should be tested first:

| Section      | Sources                                                                                                |
|--------------|--------------------------------------------------------------------------------------------------------|
| Global North | The Guardian, Times of Israel, Jerusalem Post, National Observer                                       |
| Global South | Al Jazeera, TASS, China Daily, People’s Daily, Global Times, Tehran Times, Mehr News, The Moscow Times |

### Tier 2: feasible through institutional access or NOW

| Section      | Sources                                                                             |
|--------------|-------------------------------------------------------------------------------------|
| Global North | New York Times, Washington Post, The Times, Haaretz, Globe and Mail, The Australian |
| Global South | News24, Daily Maverick, Meduza                                                      |

### Tier 3: use only if access is clearly permitted

Sources with stronger paywall, login, or technical access limitations should be included only via licensed databases, institutional access, or metadata-only treatment.

## 13. Suggested workflow

A robust workflow would be:

1. **Finalize source list**
   - classify by Global North/South;
   - classify by country;
   - classify by access method.

2. **Define inclusion criteria**
   - English;
   - news report;
   - 2023–present;
   - Gaza-relevant;
   - full text publicly/legally accessible.

3. **Pilot collection**
   - collect 20–50 articles per source;
   - inspect quality;
   - check paywall and bot behavior;
   - verify date parsing and text extraction.

4. **Corpus construction**
   - collect metadata;
   - collect article text only where allowed;
   - store raw and cleaned versions separately.

5. **Cleaning**
   - remove navigation, ads, captions if inappropriate;
   - normalize whitespace;
   - preserve paragraph boundaries;
   - remove duplicates.

6. **Annotation**
   - tokenize;
   - lemmatize;
   - POS tag;
   - extract content words.

7. **Keyness analysis**
   - compare North vs South;
   - possibly compare each source against the rest;
   - identify candidate lexical variables.

8. **LMDA**
   - build document-by-lemma matrix;
   - normalize frequencies;
   - filter rare/common lemmas;
   - run factor analysis;
   - rotate factors;
   - interpret dimensions.

9. **Validation**
   - inspect high-loading lemmas;
   - inspect high-scoring texts;
   - compare across sources and time periods;
   - verify dimensions are not artifacts of source, date, or genre.

10. **Documentation**
   - publish corpus metadata;
   - publish collection protocol;
   - publish code/workflow if possible;
   - avoid publishing copyrighted full texts unless licensed.

## 14. Possible refinement of the research question

The current project could be sharpened into something like:

> How do English-language news outlets associated with Global North and Global South geopolitical positions differ lexically in their reporting on Gaza from 2023 onward, and what discourse dimensions emerge from these differences through Lexical Multidimensional Analysis?

Or:

> What lexical-discursive dimensions distinguish Global North and Global South English-language news coverage of Gaza after October 2023?

This makes the study more operational and less vulnerable to overgeneralization.

## 15. Main risks

The main risks are:

1. **Paywall bias**  
   Some Global North sources may be underrepresented if full text is inaccessible.

2. **State-media bias**  
   Some Global South sources are state-affiliated; this should be addressed, not hidden.

3. **Genre contamination**  
   Mixing news reports with opinion pieces may distort lexical dimensions.

4. **Syndication duplication**  
   Reuters/AP/AFP copies can dominate the data.

5. **English-language bias**  
   English-language Global South media may not represent domestic discourse.

6. **Source imbalance**  
   If one source contributes far more articles, LMDA may identify source style rather than geopolitical discourse.

7. **Temporal bias**  
   Coverage in October–December 2023 may overwhelm later periods.

## 16. My recommendation

I would proceed, but with a **pilot-first design**.

Start with a small, ethically collectable pilot corpus:

| Section      | Suggested pilot sources                                              |
|--------------|----------------------------------------------------------------------|
| Global North | The Guardian, Times of Israel, Jerusalem Post, National Observer     |
| Global South | Al Jazeera, TASS, China Daily, Global Times, Tehran Times, Mehr News |

Collect perhaps:

- 50 articles per source;
- from 7 October 2023 onward;
- only full-text publicly accessible news reports;
- using `gaza` as the required seed term.

Then evaluate:

- article availability;
- metadata consistency;
- duplicate rate;
- article length;
- lexical quality after cleaning;
- balance between sections.

If the pilot works, expand to the full 2023–present period and add NOW Corpus or institutional database sources.

## Bottom line

Yes — the project is viable and academically relevant. But I would treat web scraping as only one part of the corpus-building strategy. The safest and strongest design would combine:

1. **NOW Corpus extraction where available**;
2. **licensed database access for paywalled sources**;
3. **ethical scraping only for publicly accessible pages**;
4. **strict genre, date, source, and duplication controls**;
5. **transparent documentation of access limitations**.

That will make the corpus more defensible and the LMDA results much more credible.