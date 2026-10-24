package dev.warpbound.quest;

/** Сюжетные флаги, которые ставит код. Квесты ссылаются на них в JSON по строке. */
public final class StoryFlags {
    public static final String INTRO_SHOWN = "intro_shown";
    public static final String OPENED_QUEST_BOOK = "opened_quest_book";
    public static final String SAW_NIGHT = "saw_night";
    public static final String FIRST_NIGHT = "first_night";
    public static final String BEACON_REPAIRED = "beacon_repaired";
    public static final String OPERATOR_ARRIVED = "operator_arrived";
    /** Шёпот третьего дня: после него в окне квестов появляется закрытая вкладка Хаоса. */
    public static final String CHAOS_WHISPER = "chaos_whisper";
    /** Какой путь выбран у маяка: освятил знак или осквернил. */
    public static final String PATH_MECHANICUS = "path_mechanicus";
    public static final String PATH_DARK_MECHANICUM = "path_dark_mechanicum";

    /** Сезон 1: стапель освящён и корабль стартовал с верфи. */
    public static final String SHIPYARD_FORMED = "shipyard_formed";
    public static final String SHIP_LAUNCHED = "ship_launched";

    private StoryFlags() {
    }
}
