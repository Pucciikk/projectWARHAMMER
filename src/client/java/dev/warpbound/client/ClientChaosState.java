package dev.warpbound.client;

import dev.warpbound.chaos.ChaosData;

/** Последние данные Хаоса, присланные сервером. Только для отображения. */
public final class ClientChaosState {
    private static ChaosData data = ChaosData.EMPTY;

    private ClientChaosState() {
    }

    public static ChaosData get() {
        return data;
    }

    static void set(ChaosData value) {
        data = value;
    }

    static void reset() {
        data = ChaosData.EMPTY;
    }
}
