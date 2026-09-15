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

Return valid JSON only. Do not include Markdown, code fences, comments, or explanatory text outside the JSON object. Do not wrap the JSON response in a Markdown code block.

Use exactly the following JSON structure observing:

- For fields with alternatives separated by "|", choose exactly one allowed value; do not return the alternatives themselves.
- Use a confidence value between 0.0 and 1.0.
- Set "recommended_for_main_corpus" to true only for CORE articles; otherwise set it to false.

```json
{
  "category": "CORE | PERIPHERAL | EXCLUDE",
  "confidence": 0.0,
  "gaza_role": "central | substantial | background | passing | boilerplate_or_unrelated",
  "main_topic": "...",
  "conflict_relevance": "...",
  "reason": "...",
  "multi_article_or_snippet_issue": false,
  "recommended_for_main_corpus": false
}
```

Article text:

<article>
<<<ARTICLE_TEXT>>>
</article>