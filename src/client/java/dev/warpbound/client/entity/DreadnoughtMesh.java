package dev.warpbound.client.entity;

import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;

/**
 * СГЕНЕРИРОВАНО tools/dreadnought/gen.py — правьте модель там, а не здесь.
 */
public final class DreadnoughtMesh {
    private DreadnoughtMesh() {
    }

    @SuppressWarnings("unused")
    public static LayerDefinition create() {
        MeshDefinition mesh = new MeshDefinition();
        PartDefinition root = mesh.getRoot();
        PartDefinition body = root.addOrReplaceChild("body", CubeListBuilder.create()
                        .texOffs(0, 0).addBox(-9F, -3F, -6F, 18F, 8F, 12F)
                        .texOffs(60, 0).addBox(-10F, -4F, -7F, 20F, 3F, 14F)
                        .texOffs(128, 0).addBox(-5F, -1F, -10F, 3F, 10F, 1F)
                        .texOffs(136, 0).addBox(-5F, -2F, -9F, 10F, 9F, 2F),
                PartPose.offset(0F, -6F, 0F));
        PartDefinition leg_r = body.addOrReplaceChild("leg_r", CubeListBuilder.create()
                        .texOffs(160, 0).addBox(-4F, -4F, -4F, 8F, 8F, 8F)
                        .texOffs(192, 0).addBox(-5F, 2F, -5F, 10F, 12F, 10F),
                PartPose.offset(-10F, 2F, 0F));
        PartDefinition shin_r = leg_r.addOrReplaceChild("shin_r", CubeListBuilder.create()
                        .texOffs(0, 22).addBox(-4F, -1F, -4F, 8F, 13F, 8F)
                        .texOffs(32, 22).addBox(-5F, -4F, -6F, 10F, 8F, 3F)
                        .texOffs(58, 22).addBox(-3F, 4F, 4F, 6F, 6F, 2F),
                PartPose.offset(0F, 13F, -1F));
        PartDefinition foot_r = shin_r.addOrReplaceChild("foot_r", CubeListBuilder.create()
                        .texOffs(74, 22).addBox(-6F, -1F, -9F, 12F, 4F, 15F)
                        .texOffs(128, 22).addBox(-5F, 0F, -12F, 10F, 3F, 3F),
                PartPose.offset(0F, 12F, 0F));
        PartDefinition leg_l = body.addOrReplaceChild("leg_l", CubeListBuilder.create()
                        .texOffs(154, 22).addBox(-4F, -4F, -4F, 8F, 8F, 8F)
                        .texOffs(186, 22).addBox(-5F, 2F, -5F, 10F, 12F, 10F),
                PartPose.offset(10F, 2F, 0F));
        PartDefinition shin_l = leg_l.addOrReplaceChild("shin_l", CubeListBuilder.create()
                        .texOffs(0, 44).addBox(-4F, -1F, -4F, 8F, 13F, 8F)
                        .texOffs(32, 44).addBox(-5F, -4F, -6F, 10F, 8F, 3F)
                        .texOffs(58, 44).addBox(-3F, 4F, 4F, 6F, 6F, 2F),
                PartPose.offset(0F, 13F, -1F));
        PartDefinition foot_l = shin_l.addOrReplaceChild("foot_l", CubeListBuilder.create()
                        .texOffs(74, 44).addBox(-6F, -1F, -9F, 12F, 4F, 15F)
                        .texOffs(128, 44).addBox(-5F, 0F, -12F, 10F, 3F, 3F),
                PartPose.offset(0F, 12F, 0F));
        PartDefinition torso = body.addOrReplaceChild("torso", CubeListBuilder.create()
                        .texOffs(154, 44).addBox(-13F, -26F, -10F, 26F, 26F, 20F)
                        .texOffs(0, 90).addBox(-8F, -16F, -13F, 16F, 14F, 3F)
                        .texOffs(38, 90).addBox(-10F, -24F, -12F, 20F, 3F, 2F)
                        .texOffs(82, 90).addBox(-12F, -28F, -9F, 24F, 2F, 18F)
                        .texOffs(166, 90).addBox(-10F, -35F, 6F, 4F, 14F, 4F)
                        .texOffs(182, 90).addBox(6F, -35F, 6F, 4F, 14F, 4F)
                        .texOffs(198, 90).addBox(-11F, -37F, 5F, 6F, 2F, 6F)
                        .texOffs(222, 90).addBox(5F, -37F, 5F, 6F, 2F, 6F)
                        .texOffs(0, 110).addBox(-8F, -22F, 10F, 16F, 16F, 5F)
                        .texOffs(42, 110).addBox(9F, -15F, -11F, 3F, 10F, 1F),
                PartPose.offset(0F, -3F, 0F));
        PartDefinition head = torso.addOrReplaceChild("head", CubeListBuilder.create()
                        .texOffs(50, 110).addBox(-4F, -5F, -5F, 8F, 5F, 8F)
                        .texOffs(82, 110).addBox(-3F, -3F, -6F, 6F, 2F, 1F),
                PartPose.offset(0F, -26F, -4F));
        PartDefinition arm_r = torso.addOrReplaceChild("arm_r", CubeListBuilder.create()
                        .texOffs(96, 110).addBox(-9F, -7F, -8F, 12F, 11F, 16F)
                        .texOffs(152, 110).addBox(-6F, 3F, -5F, 8F, 8F, 10F),
                PartPose.offset(-17F, -18F, 0F));
        PartDefinition gun = arm_r.addOrReplaceChild("gun", CubeListBuilder.create()
                        .texOffs(188, 110).addBox(-5F, -4F, -7F, 10F, 10F, 14F)
                        .texOffs(236, 110).addBox(-8F, -3F, -1F, 3F, 8F, 7F)
                        .texOffs(0, 137).addBox(-3F, 6F, -4F, 6F, 2F, 7F)
                        .texOffs(26, 137).addBox(-3F, -2F, -25F, 6F, 6F, 18F)
                        .texOffs(74, 137).addBox(-4F, -3F, -28F, 8F, 8F, 3F)
                        .texOffs(96, 137).addBox(-2F, -5F, -18F, 4F, 1F, 10F),
                PartPose.offset(-2F, 11F, 0F));
        PartDefinition arm_l = torso.addOrReplaceChild("arm_l", CubeListBuilder.create()
                        .texOffs(124, 137).addBox(-3F, -7F, -8F, 12F, 11F, 16F)
                        .texOffs(180, 137).addBox(-2F, 3F, -5F, 8F, 8F, 10F),
                PartPose.offset(17F, -18F, 0F));
        PartDefinition fist = arm_l.addOrReplaceChild("fist", CubeListBuilder.create()
                        .texOffs(0, 164).addBox(-5F, -2F, -6F, 10F, 12F, 12F)
                        .texOffs(44, 164).addBox(-6F, 10F, -7F, 12F, 10F, 13F)
                        .texOffs(94, 164).addBox(-6F, 20F, -7F, 3F, 5F, 4F)
                        .texOffs(108, 164).addBox(-2F, 20F, -7F, 3F, 5F, 4F)
                        .texOffs(122, 164).addBox(2F, 20F, -7F, 3F, 5F, 4F)
                        .texOffs(136, 164).addBox(-7F, 13F, -9F, 3F, 5F, 3F)
                        .texOffs(148, 164).addBox(5F, 11F, -4F, 2F, 6F, 8F),
                PartPose.offset(2F, 11F, 0F));
        return LayerDefinition.create(mesh, 256, 256);
    }
}
