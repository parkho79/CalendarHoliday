import kotlinx.serialization.Serializable

@Serializable
data class HolidayEntry(val date: String, val name: String)

@Serializable
data class HolidayMeta(val country: String, val version: Int)

@Serializable
data class HolidayFile(
    val meta: HolidayMeta,
    val holidays: Map<String, List<HolidayEntry>>,
)

@Serializable
data class CountryList(
    val nager: List<String> = emptyList(),
    val google: List<String> = emptyList(),
)
