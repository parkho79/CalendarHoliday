/** update_holidays.py의 write_json()과 정확히 같은 포맷으로 직렬화한다(공휴일 한 건 = 한 줄,
 * 2칸 들여쓰기) — kotlinx.serialization의 기본 prettyPrint(필드별 줄바꿈, 4칸)를 쓰면 실제
 * 파이프라인 출력물(holiday_list_*.json)과 형식이 달라져서 git diff가 지저분해짐. */
fun formatHolidayFile(countryCode: String, holidaysByYear: Map<String, List<HolidayEntry>>): String {
    fun escape(text: String) = text.replace("\\", "\\\\").replace("\"", "\\\"")

    val lines = mutableListOf(
        "{",
        "  \"meta\": {",
        "    \"country\": \"${countryCode.uppercase()}\",",
        "    \"version\": 1",
        "  },",
        "  \"holidays\": {",
    )

    val years = holidaysByYear.keys.toList()
    years.forEachIndexed { i, year ->
        lines.add("    \"$year\": [")
        val days = holidaysByYear.getValue(year)
        days.forEachIndexed { j, day ->
            val comma = if (j < days.size - 1) "," else ""
            lines.add("      { \"date\": \"${escape(day.date)}\", \"name\": \"${escape(day.name)}\" }$comma")
        }
        val yearComma = if (i < years.size - 1) "," else ""
        lines.add("    ]$yearComma")
    }

    lines.add("  }")
    lines.add("}")

    return lines.joinToString("\n") + "\n"
}
