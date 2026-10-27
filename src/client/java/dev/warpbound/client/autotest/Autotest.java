package dev.warpbound.client.autotest;

import com.mojang.logging.LogUtils;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.message.v1.ClientReceiveMessageEvents;
import net.fabricmc.fabric.api.client.screen.v1.ScreenEvents;
import net.fabricmc.fabric.api.client.screen.v1.Screens;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.components.AbstractWidget;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.BackupConfirmScreen;
import net.minecraft.network.chat.contents.TranslatableContents;
import net.minecraft.client.Screenshot;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.client.gui.screens.AccessibilityOnboardingScreen;
import net.minecraft.client.server.IntegratedServer;
import net.minecraft.client.tutorial.TutorialSteps;
import net.minecraft.server.level.ServerPlayer;
import org.slf4j.Logger;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.LocalTime;
import java.util.List;
import java.util.Locale;

/**
 * Автотест в живом клиенте: без участия человека открывает тестовый мир, выполняет сценарий
 * tools/autotest/&lt;имя&gt;.txt (папка — свойство -Dwarpbound.autotest.dir, без него run/autotest/)
 * и закрывает игру. Включается только свойством -Dwarpbound.autotest=&lt;имя&gt;
 * (задача ./gradlew runAutotest -Pscenario=&lt;имя&gt;), в обычной игре ничего не делает.
 *
 * Строки сценария:
 *   wait &lt;тики&gt;          подождать (20 тиков = 1 секунда)
 *   cmd &lt;команда&gt;        выполнить команду на сервере от имени игрока с правами оператора (без «/»)
 *   look &lt;yaw&gt; &lt;pitch&gt;   повернуть камеру
 *   hud on|off           показать/скрыть интерфейс
 *   clearchat            очистить чат, чтобы не закрывал кадр
 *   shot &lt;имя&gt;           скриншот в run/screenshots/autotest/&lt;сценарий&gt;/&lt;имя&gt;.png
 *   press &lt;текст&gt;        нажать кнопку открытого экрана мода с этим текстом
 *   close                закрыть открытый экран
 *   log &lt;текст&gt;          записать строку в лог
 *   quit                 выйти из игры (иначе выходим после последней строки)
 *   handover             отдать управление игроку и не выходить (осмотр вживую)
 *   use                  ПКМ предметом в главной руке (выстрел лазганом и т. п.)
 *   camera first|back|front  вид от первого лица или со спины / спереди
 *   # ...                комментарий
 * Лог (команды, все сообщения чата, ошибки) — run/autotest/&lt;сценарий&gt;.log.
 */
public final class Autotest {
    private static final Logger LOG = LogUtils.getLogger();
    public static final String WORLD = "wb_autotest";
    /** Пауза после входа в мир, чтобы прогрузились чанки и пришли пакеты синхронизации. */
    private static final int SETTLE_TICKS = 60;
    /** Сторож: зависший клиент (ошибка, неожиданный экран) закрывается сам. */
    private static final int TIMEOUT_TICKS = Integer.getInteger("warpbound.autotest.timeout", 600) * 20;
    private static int totalTicks;

    private static String scenario;
    private static List<String> lines = List.of();
    private static Path logFile;
    private static int cursor;
    private static int waitTicks;
    private static boolean worldRequested;
    private static boolean started;
    private static boolean finished;

    private Autotest() {
    }

    public static boolean active() {
        return scenario != null;
    }

    public static void register() {
        scenario = System.getProperty("warpbound.autotest");
        if (scenario == null || scenario.isBlank()) {
            scenario = null;
            return;
        }
        Minecraft mc = Minecraft.getInstance();
        Path logDir = mc.gameDirectory.toPath().resolve("autotest");
        String scriptDir = System.getProperty("warpbound.autotest.dir");
        Path script = (scriptDir != null ? Path.of(scriptDir) : logDir).resolve(scenario + ".txt");
        logFile = logDir.resolve(scenario + ".log");
        try {
            Files.createDirectories(logDir);
            Files.writeString(logFile, "", StandardCharsets.UTF_8);
            lines = Files.readAllLines(script, StandardCharsets.UTF_8);
        } catch (IOException e) {
            log("ОШИБКА: не прочитан сценарий " + script + ": " + e);
            lines = List.of("quit");
        }
        log("Сценарий " + scenario + ", строк: " + lines.size());

        // Первый экран (титульный или знакомство со специальными возможностями) — сразу в тестовый мир
        ScreenEvents.AFTER_INIT.register((client, screen, width, height) -> {
            // Измерение интерьеров корабля делает мир «экспериментальным» — подтверждаем загрузку без резервной копии
            if (screen instanceof BackupConfirmScreen) {
                for (AbstractWidget widget : Screens.getButtons(screen)) {
                    if (widget instanceof Button button && button.getMessage().getContents()
                            instanceof TranslatableContents tr && tr.getKey().equals("selectWorld.backupJoinSkipButton")) {
                        log("Мир экспериментальный — подтверждаю загрузку");
                        client.execute(button::onPress);
                    }
                }
                return;
            }
            if (worldRequested) return;
            if (screen instanceof TitleScreen || screen instanceof AccessibilityOnboardingScreen) {
                worldRequested = true;
                // Окно может быть не в фокусе — игра не должна вставать на паузу; подсказки обучения мешают кадру
                client.options.pauseOnLostFocus = false;
                client.options.tutorialStep = TutorialSteps.NONE;
                client.execute(() -> AutotestWorld.open(client));
            }
        });
        ClientReceiveMessageEvents.GAME.register((message, overlay) -> {
            if (!overlay) log("чат: " + message.getString());
        });
        ClientReceiveMessageEvents.CHAT.register((message, signed, sender, params, receivedAt) ->
                log("чат: " + message.getString()));
        ClientTickEvents.END_CLIENT_TICK.register(Autotest::tick);
    }

    private static void tick(Minecraft mc) {
        if (finished) return;
        if (++totalTicks > TIMEOUT_TICKS) {
            log("ОШИБКА: сценарий не завершился за " + TIMEOUT_TICKS / 20 + " с, выход по таймауту");
            quit(mc);
            return;
        }
        // экраны мода (пульт, книга квестов) сценарий снимает и нажимает в них кнопки; чужие — ждёт
        boolean ownScreen = mc.screen != null && mc.screen.getClass().getName().startsWith("dev.warpbound.client");
        if (mc.player == null || mc.level == null || mc.screen != null && !ownScreen) return;
        if (!started) {
            started = true;
            waitTicks = SETTLE_TICKS;
            log("Вошли в мир " + WORLD);
        }
        if (waitTicks > 0) {
            waitTicks--;
            return;
        }
        // За тик выполняем строки подряд, пока не встретим ожидание
        while (cursor < lines.size() && waitTicks == 0 && !finished) {
            run(mc, lines.get(cursor++).strip());
        }
        if (cursor >= lines.size() && waitTicks == 0 && !finished) quit(mc);
    }

    private static void run(Minecraft mc, String line) {
        if (line.isEmpty() || line.startsWith("#")) return;
        String[] parts = line.split("\\s+", 2);
        String arg = parts.length > 1 ? parts[1] : "";
        try {
            switch (parts[0].toLowerCase(Locale.ROOT)) {
                case "wait" -> waitTicks = Math.max(1, Integer.parseInt(arg));
                case "press" -> press(mc, arg);
                case "close" -> mc.setScreen(null);
                case "use" -> mc.gameMode.useItem(mc.player, net.minecraft.world.InteractionHand.MAIN_HAND);
                case "camera" -> mc.options.setCameraType(switch (arg) {
                    case "back" -> net.minecraft.client.CameraType.THIRD_PERSON_BACK;
                    case "front" -> net.minecraft.client.CameraType.THIRD_PERSON_FRONT;
                    default -> net.minecraft.client.CameraType.FIRST_PERSON;
                });
                case "cmd" -> command(mc, arg.startsWith("/") ? arg.substring(1) : arg);
                case "look" -> {
                    String[] angles = arg.split("\\s+");
                    mc.player.setYRot(Float.parseFloat(angles[0]));
                    mc.player.setXRot(Float.parseFloat(angles[1]));
                    mc.player.yRotO = mc.player.getYRot();
                    mc.player.xRotO = mc.player.getXRot();
                }
                case "hud" -> mc.options.hideGui = arg.equalsIgnoreCase("off");
                case "clearchat" -> mc.gui.getChat().clearMessages(false);
                case "shot" -> screenshot(mc, arg);
                case "log" -> log(arg);
                case "quit" -> quit(mc);
                case "handover" -> {
                    // сценарий подготовил мир — дальше играет человек, игра не закрывается
                    finished = true;
                    log("управление передано игроку");
                }
                default -> log("ОШИБКА: неизвестная строка «" + line + "»");
            }
        } catch (RuntimeException e) {
            log("ОШИБКА в строке «" + line + "»: " + e);
            LOG.error("[warpbound] autotest", e);
        }
    }

    private static void command(Minecraft mc, String command) {
        log("> " + command);
        IntegratedServer server = mc.getSingleplayerServer();
        if (server == null) {
            log("ОШИБКА: нет встроенного сервера");
            return;
        }
        var uuid = mc.player.getUUID();
        server.execute(() -> {
            ServerPlayer player = server.getPlayerList().getPlayer(uuid);
            if (player == null) return;
            server.getCommands().performPrefixedCommand(player.createCommandSourceStack().withPermission(4), command);
        });
    }

    /** Нажать кнопку открытого экрана, в надписи которой есть текст. */
    private static void press(Minecraft mc, String text) {
        if (mc.screen == null) {
            log("press: экран не открыт");
            return;
        }
        for (AbstractWidget w : Screens.getButtons(mc.screen)) {
            if (w instanceof net.minecraft.client.gui.components.Button b && b.getMessage().getString().contains(text)) {
                b.onPress();
                log("нажата кнопка «" + b.getMessage().getString() + "»");
                return;
            }
        }
        log("press: нет кнопки «" + text + "»");
    }

    private static void screenshot(Minecraft mc, String name) {
        String file = "autotest/" + scenario + "/" + name + ".png";
        try {
            Files.createDirectories(mc.gameDirectory.toPath().resolve("screenshots/autotest/" + scenario));
        } catch (IOException e) {
            log("ОШИБКА: папка скриншотов: " + e);
        }
        Screenshot.grab(mc.gameDirectory, file, mc.getMainRenderTarget(), message -> log("скриншот " + name));
    }

    private static void quit(Minecraft mc) {
        finished = true;
        log("Сценарий завершён");
        mc.stop();
    }

    static void log(String text) {
        String line = LocalTime.now().withNano(0) + " " + text;
        LOG.info("[warpbound] autotest: {}", text);
        if (logFile == null) return;
        try {
            Files.writeString(logFile, line + System.lineSeparator(), StandardCharsets.UTF_8, StandardOpenOption.APPEND);
        } catch (IOException ignored) {
            // лог автотеста не должен ронять игру
        }
    }
}
