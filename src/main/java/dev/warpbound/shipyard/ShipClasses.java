package dev.warpbound.shipyard;

import dev.warpbound.core.DataRegistry;

/** Реестр классов кораблей из data/&lt;ns&gt;/ship_class/*.json. */
public final class ShipClasses {
    public static final DataRegistry<ShipClass> REGISTRY = new DataRegistry<>("ship_class", ShipClass.CODEC);

    private ShipClasses() {
    }

    public static void register() {
    }
}
