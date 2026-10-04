import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue

/** 공휴일 한 건 — 화면에서 이름을 직접 수정할 수 있고, 수정되면 edited가 true로 바뀌어
 * 배경색이 달라진다. */
class EditableHoliday(val date: String, initialName: String) {
    var name by mutableStateOf(initialName)
    var edited by mutableStateOf(false)
}

enum class AppleYearStatus { NOT_CHECKED, UNSUPPORTED, CHECKED }

/** 한 연도 분량 — 화면에서 접고 펼 수 있고(+/-), 애플 대조 결과(그 연도를 애플이 지원하는지
 * + 날짜별로 다른 항목)를 갖는다. */
class YearGroup(val year: String, entries: List<HolidayEntry>) {
    var expanded by mutableStateOf(false)
    val holidays = mutableStateListOf<EditableHoliday>().apply {
        addAll(entries.sortedBy { it.date }.map { EditableHoliday(it.date, it.name) })
    }
    var appleStatus by mutableStateOf(AppleYearStatus.NOT_CHECKED)

    /** 애플과 다른 날짜만 담는다(날짜 -> 애플 쪽 이름들) — 요청: "애플과 다른 항목만 알려줘". */
    var appleDiffs by mutableStateOf<Map<String, Set<String>>>(emptyMap())

    val isEdited: Boolean
        get() = holidays.any { it.edited }
}
