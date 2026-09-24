"""
Batched bulk_write with checkpointing for MongoDB loads.

Processes operations in configurable batches (default: 5000) to:
1. Control memory usage on large datasets
2. Provide progress logging
3. Allow partial success (committed batches are not lost on failure)
"""
import logging
from dataclasses import dataclass, field
from typing import List

from pymongo.collection import Collection
from pymongo.operations import UpdateOne

logger = logging.getLogger(__name__)

DEFAULT_BATCH_SIZE = 5000


@dataclass
class BulkWriteResult:
    """Accumulated result of batched bulk_write operations."""
    upserted_count: int = 0
    modified_count: int = 0
    batches_completed: int = 0
    batches_total: int = 0
    errors: list = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.upserted_count + self.modified_count


def batched_bulk_write(
    collection: Collection,
    operations: List[UpdateOne],
    batch_size: int = DEFAULT_BATCH_SIZE,
    ordered: bool = False,
) -> BulkWriteResult:
    """
    Execute bulk_write in batches with progress logging.

    Instead of sending all operations at once (which can fail atomically
    and lose all progress), this processes them in chunks. Each committed
    batch is durable — a failure in batch N doesn't lose batches 1..N-1.

    Args:
        collection:  PyMongo collection object.
        operations:  List of UpdateOne (or other write) operations.
        batch_size:  Number of operations per batch.
        ordered:     Whether to execute in order within each batch.

    Returns:
        BulkWriteResult with accumulated counts and any errors.
    """
    if not operations:
        logger.warning("Nenhuma operação para executar.")
        return BulkWriteResult()

    total_ops = len(operations)
    total_batches = (total_ops + batch_size - 1) // batch_size
    result = BulkWriteResult(batches_total=total_batches)

    logger.info(
        "Bulk write: %d operações em %d batches (batch_size=%d)",
        total_ops, total_batches, batch_size,
    )

    for i in range(0, total_ops, batch_size):
        batch_num = (i // batch_size) + 1
        batch = operations[i:i + batch_size]

        try:
            res = collection.bulk_write(batch, ordered=ordered)
            result.upserted_count += res.upserted_count
            result.modified_count += res.modified_count
            result.batches_completed += 1

            if batch_num % 5 == 0 or batch_num == total_batches:
                logger.info(
                    "  Batch %d/%d concluído (acumulado: %d inseridos, %d atualizados)",
                    batch_num, total_batches,
                    result.upserted_count, result.modified_count,
                )
        except Exception as exc:
            error_msg = f"Batch {batch_num}/{total_batches} falhou: {exc}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            # Continue com próximos batches — não perder progresso
            continue

    if result.errors:
        logger.warning(
            "Bulk write concluído com %d erro(s) em %d batches.",
            len(result.errors), total_batches,
        )
    else:
        logger.info(
            "Bulk write concluído: %d inseridos + %d atualizados = %d total",
            result.upserted_count, result.modified_count, result.total,
        )

    return result
