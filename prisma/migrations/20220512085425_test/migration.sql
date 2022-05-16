BEGIN TRY

BEGIN TRAN;

-- CreateTable
CREATE TABLE [dbo].[table_info] (
    [id] BIGINT NOT NULL IDENTITY(1,1),
    [table_id] INT NOT NULL,
    [table_sub_id] INT NOT NULL,
    [item_rate] FLOAT(53) NOT NULL CONSTRAINT [table_info_item_rate_df] DEFAULT 0,
    [notice_body] NVARCHAR(1000),
    [notice_url] NVARCHAR(1000) NOT NULL CONSTRAINT [table_info_notice_url_df] DEFAULT '',
    [reg_dt] DATETIME2 NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [table_info_pkey] PRIMARY KEY ([id],[table_id])
);

-- CreateTable
CREATE TABLE [dbo].[sub_table_info] (
    [id] BIGINT NOT NULL,
    [sub_title] NVARCHAR(10) NOT NULL CONSTRAINT [sub_table_info_sub_title_df] DEFAULT '-',
    [port] INT NOT NULL,
    [item_rate] FLOAT(53) NOT NULL CONSTRAINT [sub_table_info_item_rate_df] DEFAULT 0,
    [notice_body] NVARCHAR(1000),
    [notice_url] BIT NOT NULL CONSTRAINT [sub_table_info_notice_url_df] DEFAULT 1,
    [reg_dt] DATETIME2 NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [sub_table_info_pkey] PRIMARY KEY ([id])
);

COMMIT TRAN;

END TRY
BEGIN CATCH

IF @@TRANCOUNT > 0
BEGIN
    ROLLBACK TRAN;
END;
THROW

END CATCH
