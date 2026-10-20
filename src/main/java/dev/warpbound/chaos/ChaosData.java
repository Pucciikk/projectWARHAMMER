package dev.warpbound.chaos;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

/**
 * Всё, что Хаос знает об игроке. Неизменяемая запись: любое изменение создаёт новую копию,
 * поэтому её безопасно отдавать в пакет синхронизации.
 *
 * @param corruption     порча 0..100, растёт и падает
 * @param taint          скверна 0..100, неснимаемый пол порчи
 * @param disappointment скрытое «разочарование» Империума, путь падения Астартес
 * @param khorne         благосклонность Кхорна 0..100 (и так далее для остальных)
 * @param mark           метка бога или "none"
 * @param ascension      состояние возвышения: "none", "offered", "accepted", "refused"
 */
public record ChaosData(
        float corruption,
        float taint,
        float disappointment,
        float khorne,
        float nurgle,
        float tzeentch,
        float slaanesh,
        String mark,
        String ascension
) {
    public static final ChaosData EMPTY = new ChaosData(0, 0, 0, 0, 0, 0, 0, "none", "none");

    public static final Codec<ChaosData> CODEC = RecordCodecBuilder.create(i -> i.group(
            Codec.FLOAT.optionalFieldOf("corruption", 0f).forGetter(ChaosData::corruption),
            Codec.FLOAT.optionalFieldOf("taint", 0f).forGetter(ChaosData::taint),
            Codec.FLOAT.optionalFieldOf("disappointment", 0f).forGetter(ChaosData::disappointment),
            Codec.FLOAT.optionalFieldOf("khorne", 0f).forGetter(ChaosData::khorne),
            Codec.FLOAT.optionalFieldOf("nurgle", 0f).forGetter(ChaosData::nurgle),
            Codec.FLOAT.optionalFieldOf("tzeentch", 0f).forGetter(ChaosData::tzeentch),
            Codec.FLOAT.optionalFieldOf("slaanesh", 0f).forGetter(ChaosData::slaanesh),
            Codec.STRING.optionalFieldOf("mark", "none").forGetter(ChaosData::mark),
            Codec.STRING.optionalFieldOf("ascension", "none").forGetter(ChaosData::ascension)
    ).apply(i, ChaosData::new));

    public CorruptionStage stage() {
        return CorruptionStage.of(corruption);
    }

    public float favor(ChaosGod god) {
        return switch (god) {
            case KHORNE -> khorne;
            case NURGLE -> nurgle;
            case TZEENTCH -> tzeentch;
            case SLAANESH -> slaanesh;
        };
    }

    public ChaosData withCorruption(float corruption, float taint) {
        return new ChaosData(corruption, taint, disappointment, khorne, nurgle, tzeentch, slaanesh, mark, ascension);
    }

    public ChaosData withTaint(float taint) {
        return new ChaosData(Math.max(corruption, taint), taint, disappointment, khorne, nurgle, tzeentch, slaanesh, mark, ascension);
    }

    public ChaosData withDisappointment(float value) {
        return new ChaosData(corruption, taint, value, khorne, nurgle, tzeentch, slaanesh, mark, ascension);
    }

    public ChaosData withFavor(ChaosGod god, float value) {
        return new ChaosData(corruption, taint, disappointment,
                god == ChaosGod.KHORNE ? value : khorne,
                god == ChaosGod.NURGLE ? value : nurgle,
                god == ChaosGod.TZEENTCH ? value : tzeentch,
                god == ChaosGod.SLAANESH ? value : slaanesh,
                mark, ascension);
    }

    public ChaosData withAscension(String value) {
        return new ChaosData(corruption, taint, disappointment, khorne, nurgle, tzeentch, slaanesh, mark, value);
    }
}
