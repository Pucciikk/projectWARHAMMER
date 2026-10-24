package dev.warpbound.core;

import dev.warpbound.Warpbound;
import dev.warpbound.industry.SalvageForgeMenu;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.flag.FeatureFlags;
import net.minecraft.world.inventory.MenuType;

public final class WarpboundMenus {
    public static final MenuType<SalvageForgeMenu> SALVAGE_FORGE = Registry.register(BuiltInRegistries.MENU,
            Warpbound.id("salvage_forge"), new MenuType<>(SalvageForgeMenu::new, FeatureFlags.VANILLA_SET));

    private WarpboundMenus() {
    }

    public static void register() {
    }
}
