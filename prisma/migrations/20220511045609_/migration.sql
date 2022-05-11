BEGIN TRY

BEGIN TRAN;

-- CreateTable
CREATE TABLE [dbo].[__RefactorLog] (
    [OperationKey] UNIQUEIDENTIFIER NOT NULL
);

-- CreateTable
CREATE TABLE [dbo].[achieve_data] (
    [achieve_id] INT NOT NULL,
    [quest_type] INT NOT NULL,
    [name] NVARCHAR(50) NOT NULL,
    [group_type] INT NOT NULL,
    [step_in_group] INT NOT NULL,
    [quest_todo_id] INT NOT NULL,
    [need_cnt] INT NOT NULL,
    [quest_reward_group_id] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__achieve___110170DC197E092C] PRIMARY KEY ([achieve_id])
);

-- CreateTable
CREATE TABLE [dbo].[actor_data] (
    [actor_id] INT NOT NULL,
    [name] NVARCHAR(50) NOT NULL,
    [species_type] INT NOT NULL,
    [grade] INT,
    [level] INT,
    [exp_name] NVARCHAR(20),
    [level_pattern_group_id] INT,
    [awakening_group_id] INT,
    [default_weapon] INT,
    [default_armor] INT,
    [default_accessory] INT,
    [hp] INT,
    [attack_damage] INT,
    [defense] INT,
    [ability_id_1] INT,
    [ability_id_2] INT,
    [ability_id_3] INT,
    [food_cost] INT,
    [militia_cost] INT,
    [actor_job_type] INT,
    [attack_target_type] INT,
    [attack_first_target_type] INT,
    [attack_attribute_type] INT,
    [defense_attribute_type] INT,
    [level_data_id] INT CONSTRAINT [DF__actor_dat__level__69FBBC1F] DEFAULT 0,
    [piece_item_data_id] INT CONSTRAINT [DF__actor_dat__piece__6AEFE058] DEFAULT 0,
    [status] NVARCHAR(1),
    [resource] NVARCHAR(50) CONSTRAINT [DF__actor_dat__resou__6BE40491] DEFAULT '',
    [res_folder] NVARCHAR(50) CONSTRAINT [DF__actor_dat__res_f__6CD828CA] DEFAULT '',
    [ani_num] INT,
    [sex] NVARCHAR(50) CONSTRAINT [DF__actor_data__sex__6EC0713C] DEFAULT '',
    [role_type] NVARCHAR(50) CONSTRAINT [DF__actor_dat__role___6FB49575] DEFAULT '',
    [animPrefix] NVARCHAR(50) CONSTRAINT [DF__actor_dat__animP__70A8B9AE] DEFAULT '',
    [weapon_type] INT CONSTRAINT [DF__actor_dat__weapo__719CDDE7] DEFAULT 0,
    [armor_type] INT CONSTRAINT [DF__actor_dat__armor__72910220] DEFAULT 0,
    [fx_hit] INT CONSTRAINT [DF__actor_dat__fx_hi__73852659] DEFAULT 0,
    [social_list_id] INT CONSTRAINT [DF__actor_dat__socia__74794A92] DEFAULT 0,
    [hud_dialogue_list_id] INT CONSTRAINT [DF__actor_dat__hud_d__756D6ECB] DEFAULT 0,
    [sfx_find_Target] NVARCHAR(50) CONSTRAINT [DF__actor_dat__sfx_f__76619304] DEFAULT '',
    [sfx_attack] NVARCHAR(50) CONSTRAINT [DF__actor_dat__sfx_a__7755B73D] DEFAULT '',
    [atlas_face] NVARCHAR(50) CONSTRAINT [DF__actor_dat__atlas__7849DB76] DEFAULT '',
    [face] NVARCHAR(50) CONSTRAINT [DF__actor_data__face__793DFFAF] DEFAULT '',
    [attack_speed] FLOAT(53) CONSTRAINT [DF__actor_dat__attac__7A3223E8] DEFAULT 0,
    [attack_delay] FLOAT(53) CONSTRAINT [DF__actor_dat__attac__7B264821] DEFAULT 0,
    [attack_range] FLOAT(53) CONSTRAINT [DF__actor_dat__attac__7C1A6C5A] DEFAULT 0,
    [help_attack_range] INT CONSTRAINT [DF__actor_dat__help___7D0E9093] DEFAULT 0,
    [sight_range] FLOAT(53) CONSTRAINT [DF__actor_dat__sight__7E02B4CC] DEFAULT 0,
    [sight_angle] INT CONSTRAINT [DF__actor_dat__sight__7EF6D905] DEFAULT 0,
    [walk_speed] FLOAT(53) CONSTRAINT [DF__actor_dat__walk___7FEAFD3E] DEFAULT 0,
    [run_speed] FLOAT(53) CONSTRAINT [DF__actor_dat__run_s__00DF2177] DEFAULT 0,
    [pulse_radius] INT CONSTRAINT [DF__actor_dat__pulse__01D345B0] DEFAULT 0,
    [resistant] INT CONSTRAINT [DF__actor_dat__resis__02C769E9] DEFAULT 0,
    [spawn_time] INT CONSTRAINT [DF__actor_dat__spawn__03BB8E22] DEFAULT 0,
    [evasion_rate] INT CONSTRAINT [DF__actor_dat__evasi__04AFB25B] DEFAULT 0,
    [critical_prob] INT CONSTRAINT [DF__actor_dat__criti__05A3D694] DEFAULT 0,
    [critical_damage] INT CONSTRAINT [DF__actor_dat__criti__0697FACD] DEFAULT 0,
    [piercing_prob] INT CONSTRAINT [DF__actor_dat__pierc__078C1F06] DEFAULT 0,
    [piercing_count] INT CONSTRAINT [DF__actor_dat__pierc__0880433F] DEFAULT 0,
    [endurance] INT CONSTRAINT [DF__actor_dat__endur__09746778] DEFAULT 0,
    [hit_radius] FLOAT(53) CONSTRAINT [DF__actor_dat__hit_r__0A688BB1] DEFAULT 0,
    [hit_count] INT CONSTRAINT [DF__actor_dat__hit_c__0B5CAFEA] DEFAULT 0,
    [mask_resource] NVARCHAR(50) CONSTRAINT [DF__actor_dat__mask___0C50D423] DEFAULT '',
    [disassemble_goods_type] INT CONSTRAINT [DF__actor_dat__disas__0D44F85C] DEFAULT 0,
    [model_scale] FLOAT(53) CONSTRAINT [DF__actor_dat__model__0E391C95] DEFAULT 0,
    [militia_death_prob] FLOAT(53) CONSTRAINT [DF__actor_dat__milit__0F2D40CE] DEFAULT 0,
    CONSTRAINT [PK__actor_da__8B2447B479DFADDD] PRIMARY KEY ([actor_id])
);

-- CreateTable
CREATE TABLE [dbo].[actor_level_data] (
    [actor_level_id] INT NOT NULL,
    [group_id] INT NOT NULL,
    [level] INT NOT NULL CONSTRAINT [DF__actor_lev__level__10216507] DEFAULT 0,
    [levelup_piece_cost] INT NOT NULL,
    [train_time] INT NOT NULL,
    [death_prob] SMALLINT NOT NULL CONSTRAINT [DF__actor_lev__death__11158940] DEFAULT 0,
    [goods_type1] SMALLINT NOT NULL CONSTRAINT [DF__actor_lev__goods__1209AD79] DEFAULT 0,
    [goods_count1] INT NOT NULL CONSTRAINT [DF__actor_lev__goods__12FDD1B2] DEFAULT 0,
    [goods_type2] SMALLINT NOT NULL CONSTRAINT [DF__actor_lev__goods__13F1F5EB] DEFAULT 0,
    [goods_count2] INT NOT NULL CONSTRAINT [DF__actor_lev__goods__14E61A24] DEFAULT 0,
    [item_data_id] INT NOT NULL CONSTRAINT [DF__actor_lev__item___15DA3E5D] DEFAULT 0,
    [item_count] INT NOT NULL CONSTRAINT [DF__actor_lev__item___16CE6296] DEFAULT 0,
    CONSTRAINT [PK__actor_le__540DD04D32EA284B] PRIMARY KEY ([actor_level_id])
);

-- CreateTable
CREATE TABLE [dbo].[attack_count_data] (
    [attack_count_id] INT NOT NULL,
    [reduce_time] INT NOT NULL,
    CONSTRAINT [PK__attack_c__A17E537FFDE956E9] PRIMARY KEY ([attack_count_id])
);

-- CreateTable
CREATE TABLE [dbo].[attack_extort_data] (
    [attack_extort_id] INT NOT NULL,
    [shelter_id] INT NOT NULL,
    [extort_priority] INT NOT NULL,
    [item_id] INT NOT NULL,
    [extort_amount_per] INT NOT NULL,
    [extort_amount_min] INT NOT NULL,
    [extort_amount_max] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    [reg_dt] DATETIME2 NOT NULL
);

-- CreateTable
CREATE TABLE [dbo].[attack_pre_season] (
    [user_no] BIGINT NOT NULL,
    [season_no] INT NOT NULL,
    [nick_name] NVARCHAR(50) NOT NULL,
    [trophy] INT NOT NULL,
    [attack_rank] INT NOT NULL,
    [season_rank] INT CONSTRAINT [DF__attack_pr__seaso__17C286CF] DEFAULT 0,
    [reg_dt] DATETIME2 NOT NULL,
    [attack_win] INT NOT NULL,
    [defense_win] INT CONSTRAINT [DF__attack_pr__defen__18B6AB08] DEFAULT 0,
    CONSTRAINT [PK__attack_p__4101B7B914732138] PRIMARY KEY ([season_no],[user_no])
);

-- CreateTable
CREATE TABLE [dbo].[attack_rank_data] (
    [attack_rank_id] INT NOT NULL,
    [rank_type] INT NOT NULL,
    [pre_grade] INT NOT NULL,
    [trophy] INT NOT NULL,
    [degrade] INT NOT NULL,
    [need_food_point] INT NOT NULL,
    [bonus_wood_point] INT NOT NULL,
    [bonus_parts_point] INT NOT NULL,
    [bonus_food_point] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__attack_r__A8DC19D385E4F7C6] PRIMARY KEY ([attack_rank_id])
);

-- CreateTable
CREATE TABLE [dbo].[attack_score_data] (
    [attack_score_id] INT NOT NULL,
    [win] INT NOT NULL,
    [lose] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__attack_s__22BA53F813BE760B] PRIMARY KEY ([attack_score_id])
);

-- CreateTable
CREATE TABLE [dbo].[attack_season] (
    [user_no] BIGINT NOT NULL,
    [season_no] INT NOT NULL,
    [nick_name] NVARCHAR(50) NOT NULL,
    [trophy] INT NOT NULL,
    [attack_rank] INT NOT NULL,
    [season_rank] INT CONSTRAINT [DF__attack_se__seaso__19AACF41] DEFAULT 0,
    [reg_dt] DATETIME2 NOT NULL,
    [wall_dt] DATETIME2 NOT NULL,
    [attack_win] INT NOT NULL,
    [defense_win] INT CONSTRAINT [DF__attack_se__defen__1A9EF37A] DEFAULT 0,
    [uuid] NVARCHAR(50) NOT NULL,
    CONSTRAINT [PK__attack_s__B9B1F225EBB95838] PRIMARY KEY ([user_no])
);

-- CreateTable
CREATE TABLE [dbo].[attack_season_data] (
    [attack_season_id] INT NOT NULL,
    [name] NVARCHAR(50) NOT NULL,
    [season_id] INT NOT NULL,
    [start_dt] DATETIME2 NOT NULL,
    [end_dt] DATETIME2 NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__attack_s__2DCDF7D5B054275C] PRIMARY KEY ([attack_season_id])
);

-- CreateTable
CREATE TABLE [dbo].[awakening_data] (
    [awakening_id] INT NOT NULL,
    [group_id] INT NOT NULL,
    [level] INT NOT NULL,
    [actor_level] INT NOT NULL,
    [hp] INT NOT NULL,
    [defense] INT NOT NULL,
    [attack_damage] INT NOT NULL,
    [food_cost] INT NOT NULL,
    [mat1_item_id] INT NOT NULL,
    [mat1_count] INT NOT NULL,
    [mat2_item_id] INT NOT NULL,
    [mat2_count] INT NOT NULL,
    [mat3_item_id] INT NOT NULL,
    [mat3_count] INT NOT NULL,
    [mat4_item_id] INT NOT NULL,
    [mat4_count] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__awakenin__66C414CDE6049A17] PRIMARY KEY ([awakening_id])
);

-- CreateTable
CREATE TABLE [dbo].[battle_mode_data] (
    [battle_mode_id] INT NOT NULL,
    [name] NVARCHAR(50) NOT NULL,
    [success_type] INT NOT NULL,
    [success_value] INT NOT NULL,
    [difficulty] INT NOT NULL,
    [pattern_id] INT NOT NULL,
    [world_skill_id] INT NOT NULL,
    [time] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    [reg_dt] DATETIME2 NOT NULL
);

-- CreateTable
CREATE TABLE [dbo].[bonus_attend_data] (
    [bonus_attend_id] INT NOT NULL,
    [attend_type] INT NOT NULL,
    [attend_group_id] INT NOT NULL,
    [day_count] INT NOT NULL,
    [reward_group_id] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__bonus_at__BAA9F08867658006] PRIMARY KEY ([bonus_attend_id])
);

-- CreateTable
CREATE TABLE [dbo].[bonus_attend_manage_data] (
    [bonus_attend_manage_id] INT NOT NULL IDENTITY(1,1),
    [attend_type] INT NOT NULL,
    [attend_group_id] INT NOT NULL,
    [start_dt] DATETIME2 NOT NULL,
    [end_dt] DATETIME2 NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__tmp_ms_x__13B0E18AD33D3F91] PRIMARY KEY ([bonus_attend_manage_id])
);

-- CreateTable
CREATE TABLE [dbo].[bonus_mileage_data] (
    [bonus_mileage_id] INT NOT NULL,
    [mileage] INT NOT NULL,
    [reward_group_id] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__bonus_mi__E565E03BBF596960] PRIMARY KEY ([bonus_mileage_id])
);

-- CreateTable
CREATE TABLE [dbo].[bonus_time_data] (
    [bonus_time_id] INT NOT NULL,
    [time_in_sec] INT NOT NULL,
    [reward_group_id] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__bonus_ti__9295944C6318BA30] PRIMARY KEY ([bonus_time_id])
);

-- CreateTable
CREATE TABLE [dbo].[bundle_data] (
    [bundle_id] INT NOT NULL,
    [type_id] INT NOT NULL,
    [product_type] INT NOT NULL,
    [product_id] INT NOT NULL,
    [count] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__bundle_d__4EEE7D55A2122693] PRIMARY KEY ([bundle_id])
);

-- CreateTable
CREATE TABLE [dbo].[call_act_list_data] (
    [call_act_list_id] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    [reg_dt] DATETIME2 NOT NULL
);

-- CreateTable
CREATE TABLE [dbo].[chapter_data] (
    [chapter_id] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__chapter___745EFE87EA1E081D] PRIMARY KEY ([chapter_id])
);

-- CreateTable
CREATE TABLE [dbo].[const_data] (
    [const_id] INT NOT NULL,
    [name] NVARCHAR(50),
    [int_value] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__const_da__B263BF5085D8EFA3] PRIMARY KEY ([const_id])
);

-- CreateTable
CREATE TABLE [dbo].[cure_data] (
    [cure_id] INT NOT NULL,
    [device_level] INT NOT NULL,
    [cure_target] INT NOT NULL,
    [value] INT NOT NULL,
    [time] INT NOT NULL,
    CONSTRAINT [PK__cure_dat__8FFC0630ABFA04F1] PRIMARY KEY ([cure_id])
);

-- CreateTable
CREATE TABLE [dbo].[cure_list_data] (
    [cure_list_id] INT NOT NULL,
    [name] NVARCHAR(50) NOT NULL,
    [cure_target] INT NOT NULL,
    [add_target1] INT NOT NULL,
    [add_time1] INT NOT NULL,
    [add_target2] INT NOT NULL,
    [add_time2] INT NOT NULL,
    [exp] INT NOT NULL,
    CONSTRAINT [PK__cure_lis__0AE3E82A4EAF06C3] PRIMARY KEY ([cure_list_id])
);

-- CreateTable
CREATE TABLE [dbo].[defense_pattern_data] (
    [defense_pattern_id] INT NOT NULL,
    [group_id] INT NOT NULL,
    [level] INT NOT NULL,
    [limit_time] INT NOT NULL,
    [reward_id] INT NOT NULL,
    [probability] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__defense___0D813BADAFF0D800] PRIMARY KEY ([defense_pattern_id])
);

-- CreateTable
CREATE TABLE [dbo].[defense_wave_data] (
    [defense_wave_id] INT NOT NULL,
    [defense_pattern_id] INT NOT NULL,
    [spawn_time] INT NOT NULL,
    [spawn_actor_id] INT NOT NULL,
    [spawn_count] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__defense___E8D470F02A59C810] PRIMARY KEY ([defense_wave_id])
);

-- CreateTable
CREATE TABLE [dbo].[device_data] (
    [device_id] INT NOT NULL,
    [name] NVARCHAR(50) NOT NULL,
    [level] INT NOT NULL,
    [type] INT NOT NULL,
    [need_shelter_extend_id] INT NOT NULL,
    [moveable] INT NOT NULL,
    [destroyable] INT NOT NULL,
    [goods_type] INT NOT NULL,
    [goods_count] INT NOT NULL,
    [goods_max_count] INT NOT NULL,
    [production_time] INT NOT NULL,
    [time] INT NOT NULL,
    [next_device_id] INT NOT NULL,
    [need_parts_point] INT NOT NULL,
    [need_food_point] INT NOT NULL,
    [need_wood_point] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    [effective_value] INT NOT NULL,
    CONSTRAINT [PK__device_d__3B085D8B68E5653F] PRIMARY KEY ([device_id])
);

-- CreateTable
CREATE TABLE [dbo].[device_setup_data] (
    [device_setup_id] INT NOT NULL,
    [device_type] INT NOT NULL,
    [user_level] INT NOT NULL,
    [count] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__device_s__2631E0BCAFEB9944] PRIMARY KEY ([device_setup_id])
);

-- CreateTable
CREATE TABLE [dbo].[disassemble_data] (
    [disassemble_id] INT NOT NULL,
    [equip_item_grade] INT NOT NULL,
    [equip_item_set] INT NOT NULL,
    [equip_item_type] INT NOT NULL,
    [result1_item_id] INT NOT NULL,
    [result1_count] INT NOT NULL,
    [result2_item_id] INT NOT NULL,
    [result2_count] INT NOT NULL,
    [result3_item_id] INT NOT NULL,
    [result3_count] INT NOT NULL,
    [result4_item_id] INT NOT NULL,
    [result4_count] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__disassem__7BB8AAEBF8F7CD30] PRIMARY KEY ([disassemble_id])
);

-- CreateTable
CREATE TABLE [dbo].[disaster_pattern_data] (
    [disaster_pattern_id] INT NOT NULL,
    [stage_id] INT NOT NULL,
    [pattern_id] INT NOT NULL,
    [type] INT NOT NULL,
    [data_id] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__disaster__337B5B5C2436FF6F] PRIMARY KEY ([disaster_pattern_id])
);

-- CreateTable
CREATE TABLE [dbo].[disaster_reward_data] (
    [disaster_reward_id] INT NOT NULL,
    [stage_id] INT NOT NULL,
    [pattern_id] INT NOT NULL,
    [gold_time] INT NOT NULL,
    [gold_item_id] INT NOT NULL,
    [gold_item_count] INT NOT NULL,
    [silver_time] INT NOT NULL,
    [silver_item_id] INT NOT NULL,
    [silver_item_count] INT NOT NULL,
    [bronze_time] INT NOT NULL,
    [bronze_item_id] INT NOT NULL,
    [bronze_item_count] INT NOT NULL,
    [fail_item_id] INT NOT NULL,
    [fail_item_count] INT NOT NULL,
    [limit_time] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__disaster__B574CFDC20E24C48] PRIMARY KEY ([disaster_reward_id])
);

-- CreateTable
CREATE TABLE [dbo].[disease_data] (
    [disease_id] INT NOT NULL,
    [name] NVARCHAR(50) NOT NULL,
    [contain_disease] INT NOT NULL,
    [end_rate] INT NOT NULL,
    [die_rate] INT NOT NULL,
    [attack_end_rate] INT NOT NULL,
    [attack_die_rate] INT NOT NULL,
    [skill_id] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__disease___15627065FCC33DD0] PRIMARY KEY ([disease_id])
);

-- CreateTable
CREATE TABLE [dbo].[enumtype_data] (
    [enumtype_id] INT NOT NULL,
    [enumtype] NVARCHAR(255) NOT NULL,
    [id] INT NOT NULL,
    [s_type] NVARCHAR(255) NOT NULL
);

-- CreateTable
CREATE TABLE [dbo].[equip_item_data] (
    [equip_item_id] INT NOT NULL,
    [equip_item_type] INT NOT NULL,
    [category] INT NOT NULL,
    [level] INT NOT NULL,
    [limit_level] INT NOT NULL,
    [damage] INT NOT NULL,
    [defense] INT NOT NULL,
    [durability] INT NOT NULL,
    [group_id] INT NOT NULL,
    [option_gacha_group_id] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__equip_it__DA94CA187227F72B] PRIMARY KEY ([equip_item_id])
);

-- CreateTable
CREATE TABLE [dbo].[equip_option_data] (
    [equip_option_id] INT NOT NULL,
    [type] INT NOT NULL,
    [value] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__equip_op__481FD6284838ED58] PRIMARY KEY ([equip_option_id])
);

-- CreateTable
CREATE TABLE [dbo].[equip_reinforce_data] (
    [equip_reinforce_id] INT NOT NULL,
    [probability] INT NOT NULL,
    [weapon_damage] INT NOT NULL,
    [armor_defense] INT NOT NULL,
    [accessory_defense] INT NOT NULL,
    [need_parts_point] INT NOT NULL,
    [need_wood_point] INT NOT NULL,
    [low_probability] INT NOT NULL,
    [medium_probability] INT NOT NULL,
    [high_probability] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__equip_re__8ADAA19C1F1953DF] PRIMARY KEY ([equip_reinforce_id])
);

-- CreateTable
CREATE TABLE [dbo].[equip_set_data] (
    [equip_set_id] INT NOT NULL,
    [option_id_2] INT NOT NULL,
    [option_id_3] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    [reg_dt] DATETIME2 NOT NULL
);

-- CreateTable
CREATE TABLE [dbo].[equip_upgrade_data] (
    [equip_upgrade_id] INT NOT NULL,
    [next_equip_id] INT NOT NULL,
    [mat1_item_id] INT NOT NULL,
    [mat1_count] INT NOT NULL,
    [mat2_item_id] INT NOT NULL,
    [mat2_count] INT NOT NULL,
    [mat3_item_id] INT NOT NULL,
    [mat3_count] INT NOT NULL,
    [mat4_item_id] INT NOT NULL,
    [mat4_count] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__equip_up__EE989A99D27E7BA3] PRIMARY KEY ([equip_upgrade_id])
);

-- CreateTable
CREATE TABLE [dbo].[exp_level_data] (
    [level] INT NOT NULL,
    [exp1] INT NOT NULL,
    [exp2] INT NOT NULL,
    [exp3] INT NOT NULL,
    [exp4] INT NOT NULL,
    [exp5] INT NOT NULL,
    [exp6] INT NOT NULL,
    [exp7] INT NOT NULL,
    [exp8] INT NOT NULL,
    [exp9] INT NOT NULL,
    [exp10] INT NOT NULL,
    CONSTRAINT [PK__exp_leve__C03A140BE8508429] PRIMARY KEY ([level])
);

-- CreateTable
CREATE TABLE [dbo].[explore_pattern_data] (
    [explore_pattern_id] INT NOT NULL,
    [map_id] INT NOT NULL,
    [pattern_id] INT NOT NULL,
    [type] INT NOT NULL,
    [data_id] INT NOT NULL,
    [reward_group_id] INT NOT NULL,
    [req_item_id_1] INT NOT NULL,
    [req_item_count_1] INT NOT NULL,
    [req_item_id_2] INT NOT NULL,
    [req_item_count_2] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__explore___7C9AFDE01BF436FB] PRIMARY KEY ([explore_pattern_id])
);

-- CreateTable
CREATE TABLE [dbo].[explore_reward_data] (
    [explore_reward_id] INT NOT NULL,
    [group_id] INT NOT NULL,
    [product_type] INT NOT NULL,
    [product_id] INT NOT NULL,
    [count] INT NOT NULL,
    [probability] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__explore___981D1178860B7A60] PRIMARY KEY ([explore_reward_id])
);

-- CreateTable
CREATE TABLE [dbo].[facility_setup_data] (
    [facility_id] INT NOT NULL,
    [facility_level] INT NOT NULL,
    [next_facility_id] INT NOT NULL,
    [facility_type] INT NOT NULL,
    [facility_install_type] INT NOT NULL,
    [facility_setup_type] INT NOT NULL,
    [need_wood_point] INT NOT NULL,
    [need_parts_point] INT NOT NULL,
    [need_gasoline_point] INT NOT NULL,
    [need_food_point] INT NOT NULL,
    [quickdone_dia_point] INT NOT NULL,
    [cost_time] INT NOT NULL,
    [condition_hqlv] INT NOT NULL,
    [gain_exp] INT NOT NULL,
    [condition_buildingid01] INT NOT NULL,
    [condition_buildingid02] INT NOT NULL,
    [count] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__facility__B2E8EAAE5A56892B] PRIMARY KEY ([facility_id])
);

-- CreateTable
CREATE TABLE [dbo].[gacha_data] (
    [gacha_id] INT NOT NULL,
    [type_id] INT NOT NULL,
    [product_type] INT NOT NULL,
    [product_id] INT NOT NULL,
    [count] INT NOT NULL,
    [probability] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__gacha_da__440191660EC8DDD3] PRIMARY KEY ([gacha_id])
);

-- CreateTable
CREATE TABLE [dbo].[grade_info_data] (
    [grade_info_data_id] INT NOT NULL,
    [grade_name_actor] NVARCHAR(50) NOT NULL,
    [grade_name_monster] NVARCHAR(50) NOT NULL,
    [skill_count] INT NOT NULL,
    [skill_value] INT NOT NULL,
    [increase_multiplier_hp] INT NOT NULL,
    [increase_multiplier_mental] INT NOT NULL,
    [increase_multiplier_resistance] INT NOT NULL,
    [increase_multiplier_str] INT NOT NULL,
    [increase_multiplier_dex] INT NOT NULL,
    [increase_multiplier_building] INT NOT NULL,
    [req_level] INT NOT NULL,
    [req_disaster_clear_count] INT NOT NULL,
    [eff_res] NVARCHAR(50) NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    [reg_dt] DATETIME2 NOT NULL
);

-- CreateTable
CREATE TABLE [dbo].[incident_data] (
    [incident_id] INT NOT NULL,
    [type] INT NOT NULL,
    [type_data_id] INT NOT NULL,
    [type_pattern_id] NVARCHAR(50) NOT NULL,
    [mission_type] INT NOT NULL,
    [chapter_id] INT NOT NULL,
    [incident_num] INT NOT NULL,
    [user_exp] INT NOT NULL,
    [survivor_exp] INT NOT NULL,
    [first_reward_group_id] INT NOT NULL,
    [clear_reward_group_id] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__incident__E6C40DA397A93E36] PRIMARY KEY ([incident_id])
);

-- CreateTable
CREATE TABLE [dbo].[item_data] (
    [item_id] INT NOT NULL,
    [name] NVARCHAR(50) NOT NULL,
    [type] INT NOT NULL,
    [material_type] INT NOT NULL,
    [grade] INT NOT NULL,
    [sellable] INT NOT NULL,
    [stack_count] INT NOT NULL CONSTRAINT [DF__item_data__stack__1B9317B3] DEFAULT 1,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__item_dat__52020FDD855963A6] PRIMARY KEY ([item_id])
);

-- CreateTable
CREATE TABLE [dbo].[level_need_item_data] (
    [level_need_item_id] INT NOT NULL,
    [item_id_1] INT NOT NULL,
    [item_count_1] INT NOT NULL,
    [item_id_2] INT NOT NULL,
    [item_count_2] INT NOT NULL,
    [item_id_3] INT NOT NULL,
    [item_count_3] INT NOT NULL,
    [item_id_4] INT NOT NULL,
    [item_count_4] INT NOT NULL,
    CONSTRAINT [PK__level_ne__BC01E86DB66264B8] PRIMARY KEY ([level_need_item_id])
);

-- CreateTable
CREATE TABLE [dbo].[level_pattern_data] (
    [level_pattern_id] INT NOT NULL,
    [group_id] INT NOT NULL CONSTRAINT [DF__level_pat__group__1C873BEC] DEFAULT 0,
    [level] INT NOT NULL CONSTRAINT [DF__level_pat__level__1D7B6025] DEFAULT 0,
    [hp] INT NOT NULL CONSTRAINT [DF__level_patter__hp__1E6F845E] DEFAULT 0,
    [attack_damage] INT NOT NULL CONSTRAINT [DF__level_pat__attac__1F63A897] DEFAULT 0,
    [defense] INT NOT NULL CONSTRAINT [DF__level_pat__defen__2057CCD0] DEFAULT 0,
    [food_cost] INT NOT NULL CONSTRAINT [DF__level_pat__food___214BF109] DEFAULT 0,
    CONSTRAINT [PK__level_pa__976D365D00C79A40] PRIMARY KEY ([level_pattern_id])
);

-- CreateTable
CREATE TABLE [dbo].[market_info] (
    [market_info_key] BIGINT NOT NULL IDENTITY(1,1),
    [market_type] INT NOT NULL,
    [os_type] INT NOT NULL,
    [app_down_url] NVARCHAR(255) NOT NULL,
    [reg_dt] DATETIME2 NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__tmp_ms_x__23424E13E4670948] PRIMARY KEY ([market_info_key])
);

-- CreateTable
CREATE TABLE [dbo].[notice_info] (
    [notice_info_key] BIGINT NOT NULL IDENTITY(1,1),
    [notice_body] NVARCHAR(255) NOT NULL,
    [notice_url] NVARCHAR(255) NOT NULL CONSTRAINT [DF__tmp_ms_xx__notic__06CD04F7] DEFAULT '',
    [reg_dt] DATETIME2 NOT NULL CONSTRAINT [DF__tmp_ms_xx__reg_d__07C12930] DEFAULT CURRENT_TIMESTAMP,
    [status] NVARCHAR(1) NOT NULL CONSTRAINT [DF__tmp_ms_xx__statu__08B54D69] DEFAULT 'A',
    CONSTRAINT [PK__tmp_ms_x__B883117DBC12E753] PRIMARY KEY ([notice_info_key])
);

-- CreateTable
CREATE TABLE [dbo].[option_gacha_data] (
    [option_gacha_id] INT NOT NULL,
    [group_id] INT NOT NULL,
    [option_id] INT NOT NULL,
    [probability] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__option_g__1483F53EDB66338A] PRIMARY KEY ([option_gacha_id])
);

-- CreateTable
CREATE TABLE [dbo].[pay_item_data] (
    [pay_item_id] INT NOT NULL,
    [type] INT NOT NULL,
    [type_value] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__pay_item__46C804C1681054B3] PRIMARY KEY ([pay_item_id])
);

-- CreateTable
CREATE TABLE [dbo].[quest_data] (
    [quest_id] INT NOT NULL,
    [todo_cnt] INT NOT NULL,
    [todo_id_1] INT NOT NULL,
    [todo_value_1] INT NOT NULL,
    [todo_id_2] INT NOT NULL,
    [todo_value_2] INT NOT NULL,
    [todo_id_3] INT NOT NULL,
    [todo_value_3] INT NOT NULL,
    [reward_group_id] INT NOT NULL,
    [exp] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__quest_da__9A0F00CDB407D73C] PRIMARY KEY ([quest_id])
);

-- CreateTable
CREATE TABLE [dbo].[quest_group_data] (
    [quest_group_id] INT NOT NULL,
    [title] NVARCHAR(50) NOT NULL,
    [repeat_group_id] INT NOT NULL,
    [expire_time] INT NOT NULL,
    [next_group_id] INT NOT NULL,
    [quest_count] INT NOT NULL,
    [quest_id_1] INT NOT NULL,
    [quest_id_2] INT NOT NULL,
    [quest_id_3] INT NOT NULL,
    [quest_id_4] INT NOT NULL,
    [quest_id_5] INT NOT NULL,
    [quest_id_6] INT NOT NULL,
    [quest_id_7] INT NOT NULL,
    [quest_id_8] INT NOT NULL,
    [quest_id_9] INT NOT NULL,
    [quest_id_10] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__quest_gr__3DE45DCC2BDD3349] PRIMARY KEY ([quest_group_id])
);

-- CreateTable
CREATE TABLE [dbo].[quest_open_data] (
    [quest_open_id] INT NOT NULL,
    [open_type] INT NOT NULL,
    [open_lv] INT NOT NULL,
    [check_type] INT NOT NULL,
    [check_value] INT NOT NULL,
    [quest_group_id] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__quest_op__614C64C495A4E898] PRIMARY KEY ([quest_open_id])
);

-- CreateTable
CREATE TABLE [dbo].[quest_reward_data] (
    [quest_reward_id] INT NOT NULL,
    [group_id] INT NOT NULL,
    [random_type] INT NOT NULL,
    [product_type] INT NOT NULL,
    [product_id] INT NOT NULL,
    [count] INT NOT NULL,
    [probability] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__quest_re__B5DE931C4ADCAA20] PRIMARY KEY ([quest_reward_id])
);

-- CreateTable
CREATE TABLE [dbo].[quest_todo_data] (
    [quest_todo_id] INT NOT NULL,
    [name] NVARCHAR(50) NOT NULL,
    [type] INT NOT NULL,
    [target_type] INT NOT NULL,
    [target_id] INT NOT NULL,
    [btn_type] INT NOT NULL,
    [goods_type] INT NOT NULL,
    [goods_count] INT,
    [quick_path_type] INT,
    [quick_path_target] NVARCHAR(20),
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__quest_to__E2D38D85B0B229A6] PRIMARY KEY ([quest_todo_id])
);

-- CreateTable
CREATE TABLE [dbo].[radio_quest_open_data] (
    [radio_quest_open_id] INT NOT NULL,
    [radio_level] INT NOT NULL,
    [user_level] INT NOT NULL,
    [shelter_id] INT NOT NULL,
    [stage_id] INT NOT NULL,
    [quest_group_id] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__radio_qu__EED07EF01F11AB15] PRIMARY KEY ([radio_quest_open_id])
);

-- CreateTable
CREATE TABLE [dbo].[ranking_reward_data] (
    [ranking_reward_id] INT NOT NULL,
    [name] NVARCHAR(50) NOT NULL,
    [group_id] INT NOT NULL,
    [start_ranking] INT NOT NULL,
    [end_ranking] INT NOT NULL,
    [reward_group_id] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__ranking___3885B2F96824BBFE] PRIMARY KEY ([ranking_reward_id])
);

-- CreateTable
CREATE TABLE [dbo].[recipe_combine_data] (
    [recipe_combine_id] INT NOT NULL,
    [device_level] INT NOT NULL,
    [result_item_id] INT NOT NULL,
    [mat1_item_id] INT NOT NULL,
    [mat1_count] INT NOT NULL,
    [mat2_item_id] INT NOT NULL,
    [mat2_count] INT NOT NULL,
    [mat3_item_id] INT NOT NULL,
    [mat3_count] INT NOT NULL,
    [mat4_item_id] INT NOT NULL,
    [mat4_count] INT NOT NULL,
    [time] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__recipe_c__F5E69E5F84AF9126] PRIMARY KEY ([recipe_combine_id])
);

-- CreateTable
CREATE TABLE [dbo].[recipe_data] (
    [recipe_id] INT NOT NULL,
    [device_type] INT NOT NULL,
    [device_level] INT NOT NULL,
    [result_item_id] INT NOT NULL,
    [result_item_grade] INT NOT NULL,
    [mat1_item_id] INT NOT NULL,
    [mat1_count] INT NOT NULL,
    [mat2_item_id] INT NOT NULL,
    [mat2_count] INT NOT NULL,
    [mat3_item_id] INT NOT NULL,
    [mat3_count] INT NOT NULL,
    [mat4_item_id] INT NOT NULL,
    [mat4_count] INT NOT NULL,
    [recipe_item_id] INT NOT NULL,
    [time] INT NOT NULL,
    [exp] INT NOT NULL,
    [cond] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__recipe_d__3571ED9BC72EA50D] PRIMARY KEY ([recipe_id])
);

-- CreateTable
CREATE TABLE [dbo].[recipe_refine_data] (
    [recipe_refine_id] INT NOT NULL,
    [device_level] INT NOT NULL,
    [result_item_id] INT NOT NULL,
    [mat_parts_point] INT NOT NULL,
    [mat_food_point] INT NOT NULL,
    [mat_wood_point] INT NOT NULL,
    [time] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__recipe_r__67F36FBDE2BA84D7] PRIMARY KEY ([recipe_refine_id])
);

-- CreateTable
CREATE TABLE [dbo].[recipe_smelt_data] (
    [recipe_smelt_id] INT NOT NULL,
    [device_level] INT NOT NULL,
    [type1_id] INT NOT NULL,
    [probability_1] INT NOT NULL,
    [type2_id] INT NOT NULL,
    [probability_2] INT NOT NULL,
    [type3_id] INT NOT NULL,
    [probability_3] INT NOT NULL,
    [mat1_item_id] INT NOT NULL,
    [mat1_count] INT NOT NULL,
    [mat2_item_id] INT NOT NULL,
    [mat2_count] INT NOT NULL,
    [mat3_item_id] INT NOT NULL,
    [mat3_count] INT NOT NULL,
    [mat4_item_id] INT NOT NULL,
    [mat4_count] INT NOT NULL,
    [need_cash] INT NOT NULL,
    [need_parts_point] INT NOT NULL,
    [need_wood_point] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__recipe_s__182980FA1A69C878] PRIMARY KEY ([recipe_smelt_id])
);

-- CreateTable
CREATE TABLE [dbo].[recipe_training_data] (
    [recipe_training_id] INT NOT NULL,
    [device_level] INT NOT NULL,
    [name] NVARCHAR(50) NOT NULL,
    [tab_menu] INT NOT NULL,
    [training_type] INT NOT NULL,
    [training_level] INT NOT NULL,
    [mat_parts_point] INT NOT NULL,
    [mat_wood_point] INT NOT NULL,
    [mat_food_point] INT NOT NULL,
    [time] INT NOT NULL,
    [skill_id] INT NOT NULL,
    [use_cost] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__recipe_t__4F7C8C062E671A81] PRIMARY KEY ([recipe_training_id])
);

-- CreateTable
CREATE TABLE [dbo].[reward_data] (
    [reward_id] INT NOT NULL,
    [group_id] INT NOT NULL,
    [random_type] INT NOT NULL,
    [product_type] INT NOT NULL,
    [product_id] INT NOT NULL,
    [count] INT NOT NULL,
    [probability] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__reward_d__3DD599BCC34942ED] PRIMARY KEY ([reward_id])
);

-- CreateTable
CREATE TABLE [dbo].[room_data] (
    [facility_id] INT NOT NULL,
    [level] INT NOT NULL,
    [facility_type] INT NOT NULL,
    [production_time] INT NOT NULL,
    [goods_type] INT NOT NULL,
    [goods_count] INT NOT NULL,
    [goods_max_count] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__room_dat__B2E8EAAE76454F65] PRIMARY KEY ([facility_id])
);

-- CreateTable
CREATE TABLE [dbo].[safetybox_bundle_data] (
    [safetybox_bundle_id] INT NOT NULL,
    [group_id] INT NOT NULL CONSTRAINT [DF__safetybox__group__22401542] DEFAULT 0,
    [safetybox_reward_data_group_id] INT NOT NULL CONSTRAINT [DF__safetybox__safet__2334397B] DEFAULT 0,
    [dice_count] INT NOT NULL CONSTRAINT [DF__safetybox__dice___24285DB4] DEFAULT 0,
    [reward_show] INT NOT NULL CONSTRAINT [DF__safetybox__rewar__251C81ED] DEFAULT 0,
    CONSTRAINT [PK__safetybo__351784A068C01B69] PRIMARY KEY ([safetybox_bundle_id])
);

-- CreateTable
CREATE TABLE [dbo].[safetybox_item_data] (
    [safetybox_item_id] INT NOT NULL,
    [unlock_time] INT NOT NULL CONSTRAINT [DF__safetybox__unloc__2610A626] DEFAULT 0,
    [masterkey_item_data_id] INT NOT NULL CONSTRAINT [DF__safetybox__maste__2704CA5F] DEFAULT 0,
    [masterkey_count] INT NOT NULL CONSTRAINT [DF__safetybox__maste__27F8EE98] DEFAULT 0,
    [safetybox_bundle_data_group_id] INT NOT NULL CONSTRAINT [DF__safetybox__safet__28ED12D1] DEFAULT 0,
    CONSTRAINT [PK__safetybo__AFA4C55B693A2EFC] PRIMARY KEY ([safetybox_item_id])
);

-- CreateTable
CREATE TABLE [dbo].[safetybox_reward_data] (
    [safetybox_reward_id] INT NOT NULL,
    [group_id] INT NOT NULL CONSTRAINT [DF__safetybox__group__29E1370A] DEFAULT 0,
    [sub_group] INT NOT NULL CONSTRAINT [DF__safetybox__sub_g__2AD55B43] DEFAULT 0,
    [product_type] INT NOT NULL CONSTRAINT [DF__safetybox__produ__2BC97F7C] DEFAULT 0,
    [product_id] INT NOT NULL CONSTRAINT [DF__safetybox__produ__2CBDA3B5] DEFAULT 0,
    [count] INT NOT NULL CONSTRAINT [DF__safetybox__count__2DB1C7EE] DEFAULT 0,
    [reward_prob] INT NOT NULL CONSTRAINT [DF__safetybox__rewar__2EA5EC27] DEFAULT 0,
    CONSTRAINT [PK__safetybo__7C097F2AC8C6C2B6] PRIMARY KEY ([safetybox_reward_id])
);

-- CreateTable
CREATE TABLE [dbo].[server_info] (
    [server_info_key] BIGINT NOT NULL IDENTITY(1,1),
    [is_maintenance] INT NOT NULL CONSTRAINT [DF__tmp_ms_xx__is_ma__0B91BA14] DEFAULT 0,
    [maintenance_body] NVARCHAR(255) NOT NULL CONSTRAINT [DF__tmp_ms_xx__maint__0C85DE4D] DEFAULT '',
    [maintenance_url] NVARCHAR(255) NOT NULL CONSTRAINT [DF__tmp_ms_xx__maint__0D7A0286] DEFAULT '',
    [server_type] INT NOT NULL,
    [game_server_ip] NVARCHAR(255) NOT NULL,
    [game_server_port] INT NOT NULL,
    [chat_server_ip] NVARCHAR(255) NOT NULL,
    [chat_server_port] INT NOT NULL,
    [reg_dt] DATETIME2 NOT NULL CONSTRAINT [DF__tmp_ms_xx__reg_d__0E6E26BF] DEFAULT CURRENT_TIMESTAMP,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__tmp_ms_x__F3BCBBF80246EDDD] PRIMARY KEY ([server_info_key])
);

-- CreateTable
CREATE TABLE [dbo].[shelter_area_data] (
    [shelter_area_id] INT NOT NULL,
    [shelter_id] INT NOT NULL,
    [move_index] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__shelter___01C3F9AC2402B39B] PRIMARY KEY ([shelter_area_id])
);

-- CreateTable
CREATE TABLE [dbo].[shelter_data] (
    [shelter_id] INT NOT NULL,
    [name] NVARCHAR(50) NOT NULL,
    [zone_id] INT NOT NULL,
    [need_level] INT NOT NULL,
    [next_shelter_id] INT NOT NULL,
    [setup_time] INT NOT NULL,
    [attack_time] INT NOT NULL,
    [attack_object_parts_point] INT NOT NULL,
    [attack_time_parts_point] INT NOT NULL,
    [attack_actor_food_point] INT NOT NULL,
    [attack_time_food_point] INT NOT NULL,
    [attack_win_medal_point] INT NOT NULL,
    [attack_lose_medal_point] INT NOT NULL,
    [max_defense_actor] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__shelter___8E649062862F4CEA] PRIMARY KEY ([shelter_id])
);

-- CreateTable
CREATE TABLE [dbo].[shelter_extend_data] (
    [shelter_extend_id] INT NOT NULL,
    [shelter_id] INT NOT NULL,
    [shelter_level] INT NOT NULL,
    [max_actor_cnt] INT NOT NULL,
    [max_inventory_cnt] INT NOT NULL,
    [extend_time] INT NOT NULL,
    [need_parts_point] INT NOT NULL,
    [need_food_point] INT NOT NULL,
    [need_wood_point] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__shelter___F9515298D6C66074] PRIMARY KEY ([shelter_extend_id])
);

-- CreateTable
CREATE TABLE [dbo].[shelter_level_data] (
    [shelter_level_id] INT NOT NULL,
    [shelter_id] INT NOT NULL,
    [device_id] INT NOT NULL,
    [unlock_level] INT NOT NULL,
    [move_index] INT NOT NULL,
    [target_level_id] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__shelter___D30AC82D1F778088] PRIMARY KEY ([shelter_level_id])
);

-- CreateTable
CREATE TABLE [dbo].[shop_manage_data] (
    [shop_manage_id] INT NOT NULL IDENTITY(1,1),
    [shop_merchandise_id] INT NOT NULL,
    [max_buy_count] INT NOT NULL CONSTRAINT [DF__tmp_ms_xx__max_b__123EB7A3] DEFAULT 0,
    [min_user_level] INT NOT NULL CONSTRAINT [DF__tmp_ms_xx__min_u__1332DBDC] DEFAULT 0,
    [max_user_level] INT NOT NULL CONSTRAINT [DF__tmp_ms_xx__max_u__14270015] DEFAULT 0,
    [start_date] DATETIME2,
    [end_date] DATETIME2,
    [status] NVARCHAR(1) NOT NULL CONSTRAINT [DF__tmp_ms_xx__statu__151B244E] DEFAULT 'A',
    [bonus_count] INT NOT NULL CONSTRAINT [DF__tmp_ms_xx__bonus__160F4887] DEFAULT 0,
    [is_new] INT NOT NULL CONSTRAINT [DF__tmp_ms_xx__is_ne__17036CC0] DEFAULT 0,
    [period_limit_type] INT NOT NULL CONSTRAINT [DF__tmp_ms_xx__perio__17F790F9] DEFAULT 0,
    CONSTRAINT [PK__tmp_ms_x__3CBFFD07379097D5] PRIMARY KEY ([shop_manage_id]),
    CONSTRAINT [UQ__tmp_ms_x__9EEF116B545BE5A1] UNIQUE ([shop_merchandise_id])
);

-- CreateTable
CREATE TABLE [dbo].[shop_merchandise_data] (
    [shop_merchandise_id] INT NOT NULL,
    [shop_type] INT NOT NULL,
    [cash_shop_category] INT NOT NULL,
    [shop_merchandise_priority] INT NOT NULL,
    [shop_goods_type] INT NOT NULL,
    [shop_goods_price] INT NOT NULL,
    [product_group_id] INT NOT NULL,
    [mileage] INT NOT NULL,
    [max_buy_count] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__shop_mer__9EEF116A5D87F607] PRIMARY KEY ([shop_merchandise_id])
);

-- CreateTable
CREATE TABLE [dbo].[shop_product_data] (
    [shop_product_id] INT NOT NULL,
    [product_group_id] INT NOT NULL,
    [product_type] INT NOT NULL,
    [product_id] INT NOT NULL,
    [count] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__shop_pro__86E1CC4956E228BB] PRIMARY KEY ([shop_product_id])
);

-- CreateTable
CREATE TABLE [dbo].[skill_data] (
    [skill_id] INT NOT NULL,
    [name] NVARCHAR(50) NOT NULL,
    [targeting_count] INT NOT NULL,
    [add1_id] INT NOT NULL,
    [linked_add_1_id] INT NOT NULL,
    [add1_val1] INT NOT NULL,
    [add1_val2] INT NOT NULL,
    [add1_val3] INT NOT NULL,
    [add2_id] INT NOT NULL,
    [linked_add_2_id] INT NOT NULL,
    [add2_val1] INT NOT NULL,
    [add2_val2] INT NOT NULL,
    [add2_val3] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__skill_da__FBBA837919630681] PRIMARY KEY ([skill_id])
);

-- CreateTable
CREATE TABLE [dbo].[skill_grade_data] (
    [skill_grade_id] INT NOT NULL,
    [skill_id] INT NOT NULL,
    [group_id] INT NOT NULL,
    [level] INT NOT NULL,
    [actor_level] INT NOT NULL,
    [mat1_item_id] INT NOT NULL,
    [mat1_count] INT NOT NULL,
    [mat2_item_id] INT NOT NULL,
    [mat2_count] INT NOT NULL,
    [mat3_item_id] INT NOT NULL,
    [mat3_count] INT NOT NULL,
    [mat4_item_id] INT NOT NULL,
    [mat4_count] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__skill_gr__3142C55D5FD01E9D] PRIMARY KEY ([skill_grade_id])
);

-- CreateTable
CREATE TABLE [dbo].[stage_data] (
    [stage_id] INT NOT NULL,
    [name] NVARCHAR(50) NOT NULL,
    [zone_id] INT NOT NULL,
    [start_dt] DATETIME2,
    [end_dt] DATETIME2,
    [day_of_week] INT NOT NULL,
    [part_time_start] INT NOT NULL,
    [part_time_end] INT NOT NULL,
    [need_gasoline_point] INT NOT NULL,
    [limit_time] INT NOT NULL,
    [exp] INT NOT NULL,
    [wave_map_1] INT NOT NULL,
    [wave_map_2] INT NOT NULL,
    [wave_map_3] INT NOT NULL,
    [wave_map_4] INT NOT NULL,
    [clear_object_id] INT NOT NULL,
    [clear_object_cnt] INT NOT NULL,
    [clear_explore_reward_group_id] INT NOT NULL,
    [bonus_explore_reward_group_id] INT NOT NULL,
    [limit_success] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__stage_da__CFC78760D39FCFB0] PRIMARY KEY ([stage_id])
);

-- CreateTable
CREATE TABLE [dbo].[storage_data] (
    [storage_data_id] INT NOT NULL,
    [disaster_resource] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    [reg_dt] DATETIME2 NOT NULL
);

-- CreateTable
CREATE TABLE [dbo].[subscribe_merchandise_data] (
    [subscribe_merchandise_id] INT NOT NULL,
    [subscribe_day] INT NOT NULL,
    [subscribe_goods_type] INT NOT NULL,
    [subscribe_goods_price] INT NOT NULL,
    [product_type] INT NOT NULL,
    [product_id] INT NOT NULL,
    [count] INT NOT NULL,
    [subscribe_product_group_id] INT NOT NULL,
    [mileage] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__subscrib__1E9DB31ADCF6252C] PRIMARY KEY ([subscribe_merchandise_id])
);

-- CreateTable
CREATE TABLE [dbo].[subscribe_product_data] (
    [subscribe_product_id] INT NOT NULL,
    [subscribe_product_group_id] INT NOT NULL,
    [day] INT NOT NULL,
    [product_group_id] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__subscrib__B70B9387C736C14C] PRIMARY KEY ([subscribe_product_id])
);

-- CreateTable
CREATE TABLE [dbo].[survey_data] (
    [survey_id] INT NOT NULL,
    [name] NVARCHAR(50) NOT NULL,
    [survey_type] INT NOT NULL,
    [need_shelter_id] INT NOT NULL,
    [start_date] DATETIME2,
    [end_date] DATETIME2,
    [time_1] INT NOT NULL,
    [time_2] INT NOT NULL,
    [time_3] INT NOT NULL,
    [duration] INT NOT NULL,
    [check_battle_power] INT NOT NULL,
    [add_risk_point] INT NOT NULL,
    [survey_time_1] INT NOT NULL,
    [survey_reward_1_cnt] INT NOT NULL,
    [survey_time_2] INT NOT NULL,
    [survey_reward_2_cnt] INT NOT NULL,
    [survey_time_3] INT NOT NULL,
    [survey_reward_3_cnt] INT NOT NULL,
    [survey_reward_group_id] INT NOT NULL,
    [add_gasoline_point] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__survey_d__9DC31A0745939A74] PRIMARY KEY ([survey_id])
);

-- CreateTable
CREATE TABLE [dbo].[survey_gacha_data] (
    [survey_gacha_id] INT NOT NULL,
    [type_id] INT NOT NULL,
    [stage_id] INT NOT NULL,
    [duration] INT NOT NULL,
    [probability] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__survey_g__43DEB2F609444AE4] PRIMARY KEY ([survey_gacha_id])
);

-- CreateTable
CREATE TABLE [dbo].[survey_reward_data] (
    [survey_reward_id] INT NOT NULL,
    [group_id] INT NOT NULL,
    [random_type] INT NOT NULL,
    [product_type] INT NOT NULL,
    [product_id] INT NOT NULL,
    [count] INT NOT NULL,
    [probability] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__survey_r__0150578686CF1C0A] PRIMARY KEY ([survey_reward_id])
);

-- CreateTable
CREATE TABLE [dbo].[survival_diary_data] (
    [survival_diary_id] INT NOT NULL,
    [diary_type] INT NOT NULL,
    [diary_category] INT NOT NULL,
    [target_id] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__survival__629F9C1CD293A8A0] PRIMARY KEY ([survival_diary_id])
);

-- CreateTable
CREATE TABLE [dbo].[survivor_piece_item_data] (
    [survivor_piece_item_id] INT NOT NULL,
    [item_data_id] INT NOT NULL,
    [actor_data_id] INT NOT NULL,
    CONSTRAINT [PK__survivor__29B6F452CEA9DFF6] PRIMARY KEY ([survivor_piece_item_id])
);

-- CreateTable
CREATE TABLE [dbo].[sysdiagrams] (
    [name] NVARCHAR(128) NOT NULL,
    [principal_id] INT NOT NULL,
    [diagram_id] INT NOT NULL,
    [version] INT,
    [definition] VARBINARY(max)
);

-- CreateTable
CREATE TABLE [dbo].[tutorial_data] (
    [tutorial_id] INT NOT NULL,
    [group_id] INT NOT NULL,
    [end_id] INT NOT NULL,
    CONSTRAINT [PK__tutorial__8D46C526DEF16044] PRIMARY KEY ([tutorial_id])
);

-- CreateTable
CREATE TABLE [dbo].[use_item_data] (
    [use_item_id] INT NOT NULL,
    [use_item_type] INT NOT NULL,
    [disease_id] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__use_item__85CAE01768EA389F] PRIMARY KEY ([use_item_id])
);

-- CreateTable
CREATE TABLE [dbo].[user_data] (
    [user_key] BIGINT NOT NULL IDENTITY(1,1),
    [uuid] NVARCHAR(50),
    [google_id] NVARCHAR(50),
    [facebook_id] NVARCHAR(50),
    [ios_id] NVARCHAR(50),
    [shard_db] INT NOT NULL CONSTRAINT [DF__tmp_ms_xx__shard__1CBC4616] DEFAULT 0,
    [reg_dt] DATETIME2 NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    [del_dt] DATETIME2,
    [block_end_dt] DATETIME2,
    [nick_name] NVARCHAR(50),
    CONSTRAINT [PK__tmp_ms_x__E1CC8CC0B5CBAA3E] PRIMARY KEY ([user_key]),
    CONSTRAINT [UQ__tmp_ms_x__7F42793132519836] UNIQUE ([uuid]),
    CONSTRAINT [UQ__tmp_ms_x__08E8937AA212E9B5] UNIQUE ([nick_name])
);

-- CreateTable
CREATE TABLE [dbo].[user_level_data] (
    [user_level_id] INT NOT NULL,
    [exp_for_next] INT NOT NULL,
    [explorepoint_max] INT NOT NULL,
    [explorepoint_reward] INT NOT NULL,
    [actor_hp_recovery] INT NOT NULL,
    [actor_stress_recovery] INT NOT NULL,
    [risk_point_max] INT NOT NULL,
    [defense_pattern_group_id] INT NOT NULL,
    [reward_group_id] INT NOT NULL,
    CONSTRAINT [PK__user_lev__E5D5B1BD2DD3C76D] PRIMARY KEY ([user_level_id])
);

-- CreateTable
CREATE TABLE [dbo].[version_check_info] (
    [version_check_info_key] BIGINT NOT NULL IDENTITY(1,1),
    [market_type] INT NOT NULL,
    [client_ver] NVARCHAR(20) NOT NULL,
    [is_update_require] INT NOT NULL CONSTRAINT [DF__tmp_ms_xx__is_up__1F98B2C1] DEFAULT 0,
    [server_type] INT NOT NULL,
    [res_ver] NVARCHAR(20) NOT NULL,
    [res_url] NVARCHAR(255) NOT NULL,
    [apply_dt] DATETIME2 NOT NULL,
    [reg_dt] DATETIME2 NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__tmp_ms_x__1FC487EDD529C614] PRIMARY KEY ([version_check_info_key])
);

-- CreateTable
CREATE TABLE [dbo].[world_data] (
    [world_id] INT NOT NULL,
    [name] NVARCHAR(50) NOT NULL,
    [world_type] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__world_da__A13EA50E4D535342] PRIMARY KEY ([world_id])
);

-- CreateTable
CREATE TABLE [dbo].[zone_data] (
    [zone_id] INT NOT NULL,
    [name] NVARCHAR(50) NOT NULL,
    [world_id] INT NOT NULL,
    [zone_type] INT NOT NULL,
    [status] NVARCHAR(1) NOT NULL,
    CONSTRAINT [PK__zone_dat__80B401DF2C87C9A0] PRIMARY KEY ([zone_id])
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
