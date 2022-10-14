CREATE TABLE `currency_points` (
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT primary key,
    `currency` enum('EURUSD', 'USDJPY', 'GBPUSD', 'AUDUSD', 'USDCAD'),
    `value` DECIMAL(12,6),
    `timestamp` int unsigned NOT NULL
);