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

```json
{
  "label": "RELEVANT | MARGINAL | IRRELEVANT",
  "confidence": 0.0-1.0,
  "reason": "Brief explanation in 1-3 sentences.",
  "gaza_role": "central | substantial | background | passing | boilerplate_or_unrelated",
  "main_topic": "Brief description of the article's main topic.",
  "keep_for_discourse_analysis": true/false
}
```

Article:

<<<ARTICLE_TEXT>>>