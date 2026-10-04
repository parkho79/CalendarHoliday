/** 국가 코드 -> 한글 국가명. update_holidays.py의 NAGER_COUNTRIES/GOOGLE_ONLY_CALENDARS에 있는
 * 국가 코드 전부(46개)를 커버한다. 드롭다운에 "KR_대한민국 (Nager)" 형식으로 표시하는 용도일
 * 뿐이라 실제 데이터 로직에는 영향 없음 — 새 국가가 추가되면 이 맵에도 추가해야 함. */
val COUNTRY_KOREAN_NAMES: Map<String, String> = mapOf(
    "kr" to "대한민국", "jp" to "일본", "cn" to "중국", "hk" to "홍콩", "id" to "인도네시아",
    "sg" to "싱가포르", "ph" to "필리핀", "au" to "호주", "nz" to "뉴질랜드",
    "us" to "미국", "ca" to "캐나다", "mx" to "멕시코", "br" to "브라질", "ar" to "아르헨티나",
    "cl" to "칠레", "co" to "콜롬비아", "pe" to "페루",
    "gb" to "영국", "ie" to "아일랜드", "fr" to "프랑스", "de" to "독일", "at" to "오스트리아",
    "ch" to "스위스", "it" to "이탈리아", "es" to "스페인", "pt" to "포르투갈", "nl" to "네덜란드",
    "be" to "벨기에", "se" to "스웨덴", "no" to "노르웨이", "dk" to "덴마크", "fi" to "핀란드",
    "ru" to "러시아", "ua" to "우크라이나", "pl" to "폴란드", "tr" to "튀르키예",
    "eg" to "이집트", "za" to "남아프리카공화국",
    "tw" to "대만", "th" to "태국", "my" to "말레이시아", "in" to "인도", "il" to "이스라엘",
    "vn" to "베트남", "sa" to "사우디아라비아", "ae" to "아랍에미리트",
)

/** "KR_대한민국 (Nager)" 형식의 드롭다운 표시 문자열을 만든다. */
fun countryDisplayName(code: String, source: String): String {
    val name = COUNTRY_KOREAN_NAMES[code] ?: code.uppercase()
    return "${code.uppercase()}_$name ($source)"
}
