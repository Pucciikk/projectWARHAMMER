package dev.warpbound.client;

import net.minecraft.client.renderer.DimensionSpecialEffects;
import net.minecraft.world.phys.Vec3;

/**
 * Эффекты измерения корабля: без облаков и ванильного неба (его заменяет WarpSkyRenderer),
 * туман окрашивается в цвет варпа.
 */
public class ShipInteriorEffects extends DimensionSpecialEffects {
    public ShipInteriorEffects() {
        super(Float.NaN, false, SkyType.NONE, false, false);
    }

    @Override
    public Vec3 getBrightnessDependentFogColor(Vec3 fogColor, float brightness) {
        float e = ClientShipState.enter();
        // Космос — почти чёрный, варп — тёмно-багровый
        return new Vec3(0.005 + 0.11 * e, 0.003 + 0.005 * e, 0.012 + 0.03 * e);
    }

    @Override
    public boolean isFoggyAt(int x, int y) {
        return false;
    }
}
