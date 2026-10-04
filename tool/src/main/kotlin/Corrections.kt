import kotlinx.serialization.ExperimentalSerializationApi
import kotlinx.serialization.json.*
import java.io.File

/**
 * holiday_corrections.json을 읽고, 새 규칙을 추가해서 다시 쓴다. 스키마는
 * update_holidays.py의 apply_corrections()가 기대하는 그대로 — _readme, 그리고 국가코드 ->
 * 규칙 배열. 규칙은 {"action": "remove"|"add"|"modify", "name": ..., "year": ..., "date": ...,
 * 선택적으로 "to"(modify용), "from_year"(remove용)}.
 */
@OptIn(ExperimentalSerializationApi::class)
object Corrections {
    private val prettyJson = Json { prettyPrint = true; prettyPrintIndent = "  " }

    private fun file(): File = File(Pipeline.repoRoot, "holiday_corrections.json")

    fun load(): JsonObject {
        val f = file()
        if (!f.exists()) return JsonObject(emptyMap())
        return Json.parseToJsonElement(f.readText()).jsonObject
    }

    fun rulesFor(countryCode: String): List<JsonObject> {
        val root = load()
        return (root[countryCode] as? JsonArray)?.map { it.jsonObject } ?: emptyList()
    }

    /** 새 add 규칙 하나를 만든다. */
    fun addRule(name: String, year: String, date: String): JsonObject = buildJsonObject {
        put("action", "add")
        put("name", name)
        put("year", year)
        put("date", date)
    }

    /** 새 remove 규칙 하나를 만든다(정확히 그 연도·날짜·이름). */
    fun removeRule(name: String, year: String, date: String): JsonObject = buildJsonObject {
        put("action", "remove")
        put("name", name)
        put("year", year)
        put("date", date)
    }

    private fun actionOrder(action: String) = when (action) {
        "remove" -> 0
        "modify" -> 1
        else -> 2
    }

    /** 승인된 규칙들을 해당 국가 목록에 추가하고, 기존 파이썬 스크립트와 같은 순서(연도 ->
     * 액션순서 -> 이름)로 정렬해서 저장한다. */
    fun appendRules(countryCode: String, newRules: List<JsonObject>) {
        if (newRules.isEmpty()) return
        val root = load().toMutableMap()
        val existing = ((root[countryCode] as? JsonArray)?.map { it.jsonObject } ?: emptyList()) + newRules
        val sorted = existing.sortedWith(
            compareBy(
                { it["year"]?.jsonPrimitive?.content ?: "0000" },
                { actionOrder(it["action"]?.jsonPrimitive?.content ?: "add") },
                { it["name"]?.jsonPrimitive?.content ?: "" },
            )
        )
        root[countryCode] = JsonArray(sorted)
        file().writeText(prettyJson.encodeToString(JsonObject.serializer(), JsonObject(root)) + "\n")
    }
}
