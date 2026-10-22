package dev.warpbound.config;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import dev.warpbound.Warpbound;
import net.fabricmc.loader.api.FabricLoader;

import java.io.IOException;
import java.io.Reader;
import java.io.Writer;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * Баланс в файле config/warpbound.json, чтобы править без перекомпиляции.
 * Если файла нет, он создаётся со значениями по умолчанию.
 */
public final class WarpboundConfig {
    // Варп-переход
    public int warpEnterSeconds = 6;
    public int warpTransitSeconds = 600;
    public int warpExitSeconds = 6;
    /** Потеря прочности Поля Геллера за минуту транзита при штиле (0..1). */
    public float fieldDrainPerMinute = 0.03f;
    /** Подзарядка Поля за минуту на орбите. */
    public float fieldRechargePerMinute = 0.1f;
    /** Во сколько раз шторм ускоряет потерю Поля при шторме 100%. */
    public float stormDrainMultiplier = 2.0f;
    /** Ниже этого Поля экипаж начинает получать порчу. */
    public float whisperFieldThreshold = 0.7f;
    /** Раз в сколько секунд начисляется порча от шёпотов. */
    public int whisperIntervalSeconds = 30;
    /** Порча за один «шёпот» при Поле = 0 (линейно меньше при более сильном Поле). */
    public float whisperCorruption = 4.0f;

    // Порча
    /** Сколько ниже порога ступени оседает в скверну при его пересечении. */
    public float taintBelowThreshold = 10.0f;

    // Корабли
    /** Расстояние между участками интерьеров в блоках. */
    public int plotSpacing = 2048;

    // Начало игры
    /** Ставить ли место крушения капсулы у спавна нового мира. */
    public boolean crashSiteEnabled = true;

    private static WarpboundConfig instance = new WarpboundConfig();

    public static WarpboundConfig get() {
        return instance;
    }

    public static void load() {
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        Path file = FabricLoader.getInstance().getConfigDir().resolve(Warpbound.MOD_ID + ".json");
        try {
            if (Files.exists(file)) {
                try (Reader reader = Files.newBufferedReader(file)) {
                    WarpboundConfig loaded = gson.fromJson(reader, WarpboundConfig.class);
                    if (loaded != null) instance = loaded;
                }
            }
            // Перезаписываем, чтобы в файле появились новые поля
            try (Writer writer = Files.newBufferedWriter(file)) {
                gson.toJson(instance, writer);
            }
        } catch (IOException | RuntimeException e) {
            Warpbound.LOG.error("Не удалось прочитать конфиг {}, беру значения по умолчанию", file, e);
            instance = new WarpboundConfig();
        }
    }
}
