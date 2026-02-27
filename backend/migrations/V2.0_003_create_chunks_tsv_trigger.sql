-- V2.0_003: content_tsv 自动更新触发器
DROP TRIGGER IF EXISTS trg_chunks_tsv ON chunks;

CREATE OR REPLACE FUNCTION chunks_tsv_trigger() RETURNS trigger AS $$
DECLARE
    title_ts TEXT;
BEGIN
    IF NEW.content IS NOT NULL AND char_length(NEW.content) >= 100 THEN
        title_ts := COALESCE(NULLIF(TRIM(COALESCE(NEW.section_title, '')), ''), ' ');
        NEW.content_tsv :=
            setweight(to_tsvector('jieba', NEW.content), 'A') ||
            setweight(to_tsvector('jieba', title_ts));
    ELSE
        NEW.content_tsv := NULL;
    END IF;
    RETURN NEW;
END
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_chunks_tsv
    BEFORE INSERT OR UPDATE ON chunks
    FOR EACH ROW EXECUTE FUNCTION chunks_tsv_trigger();
