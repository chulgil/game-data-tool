/*
  Warnings:

  - Added the required column `not_null_test` to the `table_info` table without a default value. This is not possible if the table is not empty.

*/
BEGIN TRY

BEGIN TRAN;

-- AlterTable
ALTER TABLE [dbo].[table_info] DROP CONSTRAINT [table_info_item_rate_df],
[table_info_notice_url_df];
ALTER TABLE [dbo].[table_info] ADD CONSTRAINT [table_info_item_rate_df] DEFAULT 1.1 FOR [item_rate], CONSTRAINT [table_info_notice_url_df] DEFAULT 'test' FOR [notice_url];
ALTER TABLE [dbo].[table_info] ADD [bool_test] BIT NOT NULL CONSTRAINT [table_info_bool_test_df] DEFAULT 0,
[bool_test2] BIT NOT NULL CONSTRAINT [table_info_bool_test2_df] DEFAULT 1,
[bool_test3] BIT NOT NULL CONSTRAINT [table_info_bool_test3_df] DEFAULT 0,
[not_null_test] INT NOT NULL,
[null_test] INT;

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
