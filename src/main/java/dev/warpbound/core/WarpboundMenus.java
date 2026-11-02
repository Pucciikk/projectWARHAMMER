package dev.warpbound.core;

import dev.warpbound.Warpbound;
import dev.warpbound.industry.SalvageForgeMenu;
import dev.warpbound.industry.machine.ChainMachineMenu;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.flag.FeatureFlags;
import net.minecraft.world.inventory.MenuType;

public final class WarpboundMenus {
    public static final MenuType<SalvageForgeMenu> SALVAGE_FORGE = Registry.register(BuiltInRegistries.MENU,
            Warpbound.id("salvage_forge"), new MenuType<>(SalvageForgeMenu::new, FeatureFlags.VANILLA_SET));

    public static final MenuType<ChainMachineMenu> CHAIN_MACHINE = Registry.register(BuiltInRegistries.MENU, Warpbound.id("chain_machine"),
            new net.fabricmc.fabric.api.screenhandler.v1.ExtendedScreenHandlerType<>(ChainMachineMenu::new, ChainMachineMenu.Init.CODEC));

    private WarpboundMenus() {
    }

    public static void register() {
    }
}
