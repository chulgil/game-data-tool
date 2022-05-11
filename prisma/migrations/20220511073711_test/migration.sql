/*
  Warnings:

  - You are about to drop the `__RefactorLog` table. If the table is not empty, all the data it contains will be lost.

*/
BEGIN TRY

BEGIN TRAN;

-- AlterTable
ALTER TABLE [dbo].[attack_extort_data] ADD CONSTRAINT attack_extort_data_pkey PRIMARY KEY ([attack_extort_id]);

-- AlterTable
ALTER TABLE [dbo].[battle_mode_data] ADD CONSTRAINT battle_mode_data_pkey PRIMARY KEY ([battle_mode_id]);

-- AlterTable
ALTER TABLE [dbo].[call_act_list_data] ADD CONSTRAINT call_act_list_data_pkey PRIMARY KEY ([call_act_list_id]);

-- AlterTable
ALTER TABLE [dbo].[enumtype_data] ADD CONSTRAINT enumtype_data_pkey PRIMARY KEY ([enumtype_id]);

-- AlterTable
ALTER TABLE [dbo].[equip_set_data] ADD CONSTRAINT equip_set_data_pkey PRIMARY KEY ([equip_set_id]);

-- AlterTable
ALTER TABLE [dbo].[grade_info_data] ADD CONSTRAINT grade_info_data_pkey PRIMARY KEY ([grade_info_data_id]);

-- DropTable
DROP TABLE [dbo].[__RefactorLog];

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
