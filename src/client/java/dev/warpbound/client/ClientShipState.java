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
        if (!wasAboard && aboard) {
            // Поднялись на борт посреди варпа: сразу показываем нужное небо
            enter = targetEnter();
            fieldSmooth = field;
            stormSmooth = storm;
        }
    }

    static void reset() {
        aboard = false;
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
