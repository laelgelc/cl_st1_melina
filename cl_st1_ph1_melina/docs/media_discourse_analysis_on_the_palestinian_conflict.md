# Media Discourse Analysis on the Palestinian Conflict

> User:
> 
> This research project aims to study the discourses around the palestinian conflict as portrayed by media in Global North and Global South hegemonic blocks and the discursive transformation across years 2023 to 2025. A news articles dataset was initially extracted from the NOW corpus using `gaza` as the seed term, resulting in a total of 117,519 articles.
>
> We intend to use a GPT LLM to classify the articles as relevant or irrelevant beyond the seed term `gaza`. We do not want to be too restrictive when prompting the LLM to avoid cherry picking and bias the captured discourses. But we want to avoid selecting news articles that touch `gaza` lightly.
> 
> I'd like to discuss the best prompt design in the first place.
> 
> Secondly, as cost is an issue, given the great number of articles, what would be the most cost effective way to use the GPT LLM model. Should we just choose a version that just does the job for the least cost?
>
> Attached are two articles as examples.

AI Assistant:

## 1. Prompt design: define “relevance” broadly but operationally

For your project, the key is **not** to ask the model whether an article is “about Gaza” in a narrow topical sense. That would over-select military/event reporting and under-select discourse-relevant pieces about humanitarianism, international law, media framing, protest, diplomacy, antisemitism/Islamophobia, colonialism, terrorism, etc.

Instead, I would frame relevance as:

> **Does the article contain enough substantive material related to Gaza, Palestinians, Israel/Palestine, the war, occupation, humanitarian conditions, international responses, or public discourse around these issues to plausibly contribute to a discourse analysis of the Palestinian conflict?**

This allows a broad capture of discourse while excluding articles where “Gaza” appears only incidentally.

A useful design is **three-way classification**, not binary:

1. **Relevant**  
   Gaza / Palestine / Israel-Palestine conflict is a central or substantial topic.

2. **Marginal / Tangential**  
   The article mentions Gaza or the Palestinian conflict, but only briefly, in passing, or as one example among many.

3. **Irrelevant**  
   Gaza appears only as a stray mention, boilerplate, unrelated metadata, list item, archive link, unrelated “latest stories” block, etc.

Then you can decide later whether to keep only **Relevant**, or perhaps include a stratified sample of **Marginal** articles for sensitivity analysis.

---

## 2. Recommended classification criteria

I would avoid asking the model to judge ideological “importance” or “quality.” Instead, give it concrete inclusion/exclusion rules.

### Include as **Relevant** if the article substantially discusses one or more of:

- Gaza as a place, population, territory, or political space.
- The Israel-Hamas war, Israeli military operations, Hamas, hostages, ceasefires, displacement, humanitarian crisis, blockade, aid, famine, reconstruction, hospitals, civilians, casualties.
- The broader Israeli-Palestinian conflict where Gaza is part of the argument.
- Palestinian politics, Palestinian civilians, Palestinian rights, occupation, settlements, blockade, refugees, resistance, diplomacy, statehood.
- International reactions to Gaza/Palestine/Israel: UN, ICC, ICJ, US/EU/Arab states, protests, boycotts, sanctions, media controversy.
- Discursive framings of the conflict: terrorism, genocide, apartheid, self-defence, colonialism, antisemitism, Islamophobia, humanitarianism, international law, moral equivalence, double standards.
- Articles about books, culture, speeches, protests, campus debates, or opinion pieces **if** Gaza/Palestine/Israel is discussed substantively.

### Mark as **Marginal / Tangential** if:

- Gaza is mentioned only briefly as background to a different main topic.
- The article is mainly about another conflict, person, book, cultural event, domestic politics, etc., but includes a short paragraph or two connecting it to Gaza/Palestine.
- Gaza is one item in a roundup, list, photo caption collection, or “latest stories” section.
- The article includes a relevant passage but the overall article is not primarily or substantially about the conflict.

### Mark as **Irrelevant** if:

- “Gaza” appears only in unrelated boilerplate, navigation text, old related links, comments, tags, or article recommendations.
- The article is about a completely unrelated topic and Gaza appears only once without meaningful discussion.
- The mention is geographically incidental, e.g. “mission to the West Bank and Gaza” in a bio, with no substantive conflict discussion.
- The article is a news bundle where the matching Gaza passage is clearly not the main article.

---

## 3. Important: classify the article, not just the occurrence of “Gaza”

NOW corpus files may contain multiple articles or aggregated snippets. Some examples you attached include “Latest Stories” blocks where Gaza appears in a separate unrelated item. This is crucial.

The prompt should tell the model:

> If the supplied text contains multiple article fragments, classify the **dominant article or the article associated with the title/headline**, but note if Gaza appears only in a secondary embedded item.

Alternatively, if your preprocessing can split article IDs cleanly, classify each article ID separately. That is preferable.

---

## 4. Suggested prompt template

Here is a prompt I would use for initial GPT classification.

```plain text
You are assisting a corpus-linguistics research project studying media discourses around Gaza, Palestine, Israel/Palestine, and the Palestinian conflict between 2023 and 2025.

Your task is to classify whether a news article selected by the seed term "gaza" is substantively relevant for discourse analysis.

Use the following labels:

RELEVANT:
The article contains substantive discussion of Gaza, Palestinians, Israel/Palestine, the Israel-Hamas war, occupation, blockade, humanitarian conditions, diplomacy, protests, international law, media discourse, or other issues directly connected to the Palestinian conflict. The article does not need to be only about Gaza; it may be relevant if Gaza/Palestine/Israel is an important part of the argument or framing.

MARGINAL:
The article mentions Gaza, Palestine, Palestinians, Israel/Palestine, Hamas, or the conflict only briefly, as background, comparison, a passing example, a photo caption, a book/topic among many, or in a roundup. It may contain some relevant material, but the main article is about something else.

IRRELEVANT:
The article only mentions Gaza incidentally, in boilerplate, unrelated links, unrelated "latest stories", metadata, comments, or a stray reference. It would not contribute meaningfully to discourse analysis of the Palestinian conflict.

Decision rules:
- Be inclusive when there is meaningful discourse about Gaza/Palestine/Israel.
- Do not require Gaza to be the only or main topic.
- Do not exclude opinion, cultural, book-review, protest, legal, diplomatic, or meta-discursive articles if they substantively discuss the conflict.
- Do exclude articles where Gaza appears only as a minor aside or unrelated embedded item.
- If unsure between RELEVANT and MARGINAL, choose MARGINAL.
- If unsure between MARGINAL and IRRELEVANT, choose MARGINAL only if there is at least one sentence with meaningful conflict-related content.

Return valid JSON only, with this schema:

{
  "label": "RELEVANT | MARGINAL | IRRELEVANT",
  "confidence": 0.0-1.0,
  "reason": "Brief explanation in 1-3 sentences.",
  "gaza_role": "central | substantial | background | passing | boilerplate_or_unrelated",
  "main_topic": "Brief description of the article's main topic.",
  "keep_for_discourse_analysis": true/false
}

Article:
<<<ARTICLE_TEXT>>>
```


For your purposes, I would map:

- `RELEVANT` → keep
- `MARGINAL` → maybe keep for audit sample / sensitivity analysis, or send to a stronger model for second review
- `IRRELEVANT` → discard

---

## 5. How the two attached examples would likely classify

### Example 1: Israeli troop drawdown from Gaza

This should be **RELEVANT**.

It is centrally about Gaza, Israeli military operations, civilian casualties, displacement, Hamas, US pressure, and the changing phase of the war. It is exactly the type of article your corpus should retain.

Expected output:

```json
{
  "label": "RELEVANT",
  "confidence": 0.98,
  "reason": "The article is centrally about Israeli military operations in Gaza, troop movements, Hamas, casualties, displacement, and international pressure. It provides substantive discourse about the war and humanitarian conditions.",
  "gaza_role": "central",
  "main_topic": "Israeli troop drawdown and ongoing fighting in Gaza",
  "keep_for_discourse_analysis": true
}
```


### Example 2: Naomi Klein / Naomi Wolf book review

This is more delicate. I would probably classify it as **MARGINAL**, not irrelevant.

The main article is a book review about Naomi Klein’s *Doppelganger*, online conspiracy culture, identity confusion, and the “mirror world.” However, it includes a meaningful discussion of Israel/Palestine, Gaza, Zionism, Jewish identity, backlash after criticism of Israel’s 2014 Gaza attack, and discursive polarization. For a project on media discourse, especially if interested in how Gaza appears in wider cultural and ideological debates, this may be analytically useful. But it is not centrally about Gaza.

Expected output:

```json
{
  "label": "MARGINAL",
  "confidence": 0.78,
  "reason": "The article is primarily a book review about Naomi Klein, Naomi Wolf, conspiracy culture, and online polarization. It contains a substantive but limited passage connecting these issues to Israel, Zionism, and Gaza, so it may be useful for studying broader discourse but is not centrally about Gaza.",
  "gaza_role": "background",
  "main_topic": "Book review of Naomi Klein's Doppelganger and its discussion of conspiracy culture",
  "keep_for_discourse_analysis": false
}
```


However, you could choose to keep **MARGINAL** articles separately if your project explicitly studies discursive spillover into culture-war contexts.

---

## 6. Add a “why not relevant?” instruction to reduce false positives

A common problem with seed-term corpora is that the model will over-classify anything mentioning Gaza as relevant. You can counter this by asking the model to identify the **role of Gaza**.

For example:

```plain text
Before assigning the final label, determine whether Gaza is:
1. central topic
2. substantial supporting topic
3. background context
4. passing mention
5. boilerplate/unrelated text
```


Then constrain the decision:

```plain text
Only classify as RELEVANT if Gaza/Palestine/Israel-Palestine is central or substantial.
Classify as MARGINAL if it is background or passing but still meaningful.
Classify as IRRELEVANT if it is boilerplate, unrelated, or merely an accidental match.
```


This makes the model less likely to over-include.

---

## 7. Consider two dimensions instead of one

For discourse analysis, a single relevance label may be too blunt. I would consider asking for two separate judgments:

### A. Topical relevance

Is this article substantively about Gaza/Palestine/Israel-Palestine?

### B. Discursive usefulness

Even if not centrally about Gaza, does it contain useful discourse around the conflict?

This helps with pieces like book reviews, opinion columns, culture-war articles, campus protest articles, or articles about antisemitism/Islamophobia where Gaza is not the headline topic but the discourse is relevant.

Possible output:

```json
{
  "topical_relevance": "high | medium | low | none",
  "discursive_relevance": "high | medium | low | none",
  "recommended_set": "core | peripheral | exclude"
}
```


Then:

- `core`: central conflict coverage.
- `peripheral`: relevant for broader discourse, framing, ideology, protest, comparison, culture, etc.
- `exclude`: accidental or trivial mention.

This may fit your research design better than a binary relevant/irrelevant label.

---

## 8. Suggested improved prompt with “core/peripheral/exclude”

If your goal is to avoid cherry-picking while still removing weak matches, I prefer this version:

```plain text
You are assisting a corpus-linguistics research project studying media discourses around Gaza, Palestine, Israel/Palestine, and the Palestinian conflict between 2023 and 2025.

Classify the article into one of three research-use categories:

CORE:
The article is centrally or substantially about Gaza, the Israel-Hamas war, Palestinians, Israel/Palestine, occupation, blockade, humanitarian conditions, military action, diplomacy, international law, hostages, protests, media framing, or other directly connected conflict issues.

PERIPHERAL:
The article is mainly about another subject but contains meaningful discourse related to Gaza, Palestine, Israel/Palestine, Zionism, antisemitism, Islamophobia, colonialism, terrorism, humanitarianism, international law, protests, or public debate around the conflict. These articles may be useful for studying broader discursive formations but should not be treated as core conflict coverage.

EXCLUDE:
The article contains only an incidental, boilerplate, unrelated, navigational, metadata, roundup, comment-section, or passing mention of Gaza/Palestine/Israel-Palestine. It would not meaningfully contribute to discourse analysis.

Guidelines:
- Be inclusive for CORE and PERIPHERAL when there is meaningful discourse.
- Do not require political neutrality from the article.
- Do not judge whether the article is factually correct or morally acceptable; classify only research relevance.
- If the article contains multiple unrelated snippets, classify the main article associated with the headline/title.
- If Gaza appears only in an unrelated embedded news item, mark EXCLUDE or PERIPHERAL depending on how substantive that embedded item is.
- If unsure between CORE and PERIPHERAL, choose PERIPHERAL.
- If unsure between PERIPHERAL and EXCLUDE, choose PERIPHERAL only if there is at least one meaningful sentence about the conflict.

Return JSON only:

{
  "category": "CORE | PERIPHERAL | EXCLUDE",
  "confidence": 0.0-1.0,
  "main_topic": "...",
  "conflict_relevance": "...",
  "reason": "...",
  "gaza_role": "central | substantial | background | passing | boilerplate_or_unrelated"
}

Article:
<<<ARTICLE_TEXT>>>
```


This aligns better with your stated goal: **avoid cherry-picking while avoiding articles that only touch Gaza lightly**.

---

# 9. Cost-effective GPT strategy

With 117,519 articles, sending every full article to a high-end GPT model may be unnecessarily expensive. I would not start by simply choosing “the cheapest model that works” without validation. Instead, use a **tiered pipeline**.

## Recommended approach: cascade classification

### Step 1: Rule-based filtering before GPT

Use simple heuristics to identify obvious cases.

Examples of signals for likely **CORE**:

- High frequency of terms such as `Gaza`, `Hamas`, `Israel`, `Palestinian`, `ceasefire`, `hostage`, `Rafah`, `Khan Younis`, `UNRWA`, `IDF`, `Netanyahu`, `occupation`, `blockade`.
- Gaza appears in headline or first paragraphs.
- Multiple conflict terms appear near each other.
- Article length contains several Gaza-related paragraphs.

Signals for likely **EXCLUDE**:

- Single occurrence of “Gaza.”
- Gaza appears only after phrases such as “Latest Stories,” “Related Articles,” “Read more,” “Comments,” “Most Popular.”
- Gaza appears only in a list of headlines.
- Main headline is clearly unrelated and the Gaza mention is far down in the text.
- Very low density of conflict-related terms.

This step can reduce the number of articles requiring GPT.

---

### Step 2: Use a cheap/small GPT model for first-pass classification

Use a low-cost model for all ambiguous and likely relevant cases. The task is relatively simple: topical/discursive relevance classification.

For each article, send:

- title
- date
- source/country if available
- first 800–1,500 words
- all paragraphs containing “Gaza” plus perhaps one paragraph before and after each occurrence
- optionally headline and metadata

You often do **not** need to send the whole article.

This is very important for cost. Many articles are long because of web clutter, comments, unrelated embedded stories, or appended blocks. You can classify relevance from a compressed representation.

A compact input could be:

```plain text
Title: ...
Date: ...
Source country: ...

Opening paragraphs:
...

Paragraphs containing seed term and surrounding context:
...

Task: classify CORE/PERIPHERAL/EXCLUDE.
```


This can cut token cost dramatically.

---

### Step 3: Send uncertain cases to a stronger model

Ask the first model for confidence. Then escalate only cases such as:

- confidence below 0.75
- category = PERIPHERAL
- disagreement between rule-based score and model label
- articles from underrepresented regions/sources where false exclusions would be costly
- articles where Gaza appears in complex cultural, legal, or political discourse

This gives you better quality without paying high-model prices for every article.

---

### Step 4: Human validation sample

You should manually label a statistically meaningful sample before committing to full-scale classification.

For example:

- 300–500 articles manually labeled by researchers.
- Include balanced samples from:
  - likely core
  - likely peripheral
  - likely exclude
  - Global North
  - Global South
  - 2023, 2024, 2025
  - different genres: news, opinion, culture, roundup, syndicated wire

Then evaluate:

- false exclusion rate
- false inclusion rate
- disagreement on peripheral cases
- model consistency across countries/sources
- whether Global South articles are being disproportionately excluded due to different terminology or framing

For your research, **false exclusions may be more dangerous than false inclusions**, because they can bias the discourse sample before analysis. So you may prefer a permissive classifier followed by downstream weighting or filtering.

---

## 10. Do not rely only on the cheapest model without benchmarking

The cheapest model may be fine, but you should test it against your own gold-standard sample.

I would compare at least three configurations:

1. **Cheap model, short context**
2. **Cheap model, expanded context**
3. **Stronger model, short context**

Then measure agreement with human labels.

You may find that a cheap model does well on clear **CORE** and **EXCLUDE** cases but struggles with **PERIPHERAL** discourse articles, such as the Naomi Klein example. In that case, a cascade is ideal:

- cheap model for obvious cases
- stronger model only for borderline cases

---

## 11. Use confidence and category-specific thresholds

A good cost-aware rule could be:

| First-pass result | Action |
|---|---|
| CORE, confidence ≥ 0.85 | Keep |
| EXCLUDE, confidence ≥ 0.90 | Exclude |
| PERIPHERAL | Send to second pass or keep in separate peripheral set |
| Any label, confidence < 0.80 | Send to stronger model |
| Conflict between heuristic and model | Send to stronger model |

Be especially careful with high-confidence exclusions. If the model wrongly excludes articles from certain regions or genres, you can introduce systematic bias.

---

## 12. Suggested final dataset structure

Rather than producing only one filtered corpus, I would keep three layers:

### A. Core corpus

Articles classified as **CORE**.

Use this for main quantitative discourse analysis.

### B. Peripheral corpus

Articles classified as **PERIPHERAL**.

Use this for:

- robustness checks
- qualitative discourse analysis
- comparison of how Gaza enters broader public debates
- examining cultural, ideological, or meta-discursive references

### C. Excluded corpus

Articles classified as **EXCLUDE**, but keep metadata and reasons.

Useful for auditability.

This is better research practice than permanently discarding everything not labelled relevant.

---

## 13. Recommended output fields

For each article, store:

```json
{
  "article_id": "...",
  "category": "CORE | PERIPHERAL | EXCLUDE",
  "confidence": 0.91,
  "gaza_role": "central | substantial | background | passing | boilerplate_or_unrelated",
  "main_topic": "...",
  "reason": "...",
  "model": "...",
  "prompt_version": "v1.0",
  "classification_date": "..."
}
```


Also store:

- article length
- number of “Gaza” mentions
- position of first “Gaza” mention
- count of related terms: Israel, Palestinian, Hamas, ceasefire, etc.
- whether Gaza appears in headline
- source country
- Global North / Global South label
- year/month

These features let you audit selection bias later.

---

# 14. Practical recommendation

I would use this workflow:

1. **Create a human-labeled validation sample.**
2. **Design the CORE / PERIPHERAL / EXCLUDE prompt.**
3. **Run a cheap GPT model on the validation sample.**
4. **Compare against human labels.**
5. **Adjust the prompt and thresholds.**
6. **Use a cascade:**
   - rules for obvious excludes
   - cheap GPT for most articles
   - stronger GPT for uncertain/peripheral cases
7. **Keep peripheral articles separately rather than discarding them immediately.**

This gives you a good balance between **cost**, **methodological transparency**, and **protection against selection bias**.

The main principle should be:

> Use the LLM not as an authority deciding what “matters,” but as a reproducible, audited relevance filter whose errors are measured against human-coded examples.