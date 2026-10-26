package dev.warpbound.client;

import dev.warpbound.network.ShipStatePayload;
import dev.warpbound.ship.ShipState;

/**
 * Состояние корабля, на котором стоит игрок, глазами клиента.
 * Сервер шлёт обновления раз в секунду, а рендеру нужны плавные значения каждый кадр,
 * поэтому здесь же живут сглаженные величины.
 */
public final class ClientShipState {
    /** Сколько секунд длится раскрытие разрыва. Совпадает с warpEnterSeconds по умолчанию. */
    private static final float ENTER_SECONDS = 6f;

    private static boolean aboard;
    private static ShipState state = ShipState.ORBIT;
    private static float progress;
    private static float field = 1f;
    private static float storm = 0.3f;
    private static int flight;
    /** Ход корабля 0..1: плавно растёт после запуска двигателей — по нему текут звёзды и трясёт палубу. */
    private static float cruise;
    /** Толчок запуска двигателей / раскрытия разлома 0..1, быстро гаснет. */
    private static float jolt;

    private static float enter;
    private static float fieldSmooth = 1f;
    private static float stormSmooth = 0.3f;
    private static long lastNanos;

    private ClientShipState() {
    }

    static void update(ShipStatePayload p) {
        boolean wasAboard = aboard;
        aboard = p.aboard();
        state = ShipState.byId(p.state());
        progress = p.progress();
        field = p.field();
        storm = p.storm();
        int was = flight;
        flight = p.flight();
        if ((flight & 1) != 0 && (was & 1) == 0) jolt = 1f;       // двигатели запущены
        if (state == ShipState.ENTERING && p.progress() < 0.1f) jolt = 1f;
        if (!wasAboard && aboard) {
            // Поднялись на борт посреди варпа: сразу показываем нужное небо
            enter = targetEnter();
            fieldSmooth = field;
            stormSmooth = storm;
        }
    }

    /** Разлом раскрывается: молнии бьют чаще. */
    public static boolean entering() {
        return aboard && state == ShipState.ENTERING;
    }

    public static boolean enginesOn() {
        return aboard && (flight & 1) != 0;
    }

    public static float cruise() {
        return cruise;
    }

    /** Насколько трясёт палубу сейчас: ход, толчки, раскрытие разлома. */
    public static float shake() {
        if (!aboard) return 0f;
        float warp = state == ShipState.ENTERING ? 0.8f : state == ShipState.TRANSIT ? 0.15f + 0.3f * (1f - field) : 0f;
        return Math.min(1f, 0.12f * cruise + 0.9f * jolt + warp);
    }

    static void reset() {
        aboard = false;
        flight = 0;
        cruise = 0f;
        state = ShipState.ORBIT;
        enter = 0f;
        fieldSmooth = 1f;
    }

    private static float targetEnter() {
        return switch (state) {
            case ENTERING, TRANSIT -> 1f;
            case EXITING, ORBIT -> 0f;
        };
    }

    /** Вызывается раз в кадр перед рендером неба. Возвращает прошедшее время в секундах. */
    static float advanceFrame() {
        long now = System.nanoTime();
        float dt = lastNanos == 0 ? 0f : Math.min(0.1f, (now - lastNanos) / 1e9f);
        lastNanos = now;

        float target = targetEnter();
        float step = dt / ENTER_SECONDS;
        if (enter < target) enter = Math.min(target, enter + step);
        if (enter > target) enter = Math.max(target, enter - step);

        float wantCruise = aboard && (flight & 1) != 0 ? 1f : 0f;
        cruise += (wantCruise - cruise) * (1f - (float) Math.exp(-dt * 0.25));
        jolt *= (float) Math.exp(-dt * 0.8);
        float k = 1f - (float) Math.exp(-dt * 2.0);
        fieldSmooth += (field - fieldSmooth) * k;
        stormSmooth += (storm - stormSmooth) * k;
        return dt;
    }

    public static boolean aboard() {
        return aboard;
    }

    public static ShipState state() {
        return state;
    }

    public static float progress() {
        return progress;
    }

    public static float field() {
        return fieldSmooth;
    }

    public static float storm() {
        return stormSmooth;
    }

    /** 0 — обычный космос, 1 — варп. Сглажено по времени. */
    public static float enter() {
        return enter;
    }
}
