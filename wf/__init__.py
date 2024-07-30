from wf.task import *

from latch.resources.workflow import workflow
from latch.types.directory import LatchDir, LatchOutputDir
from latch.types.file import LatchFile
from latch.types.metadata import LatchAuthor, LatchMetadata, LatchParameter
from latch.functions.operators import List
from latch.functions.operators import *

from enum import Enum


metadata = LatchMetadata(
    display_name="Colony Image Analysis",
    author=LatchAuthor(
        name="Tony Farina, Kyle Botsch, Tu-Trinh Nguyen",
    ),
    parameters={
        "JpgFiles": LatchParameter(
            display_name="Jpg Files",
            description="Jpgs of 384 Agar Plates to Cherry Pick",
            batch_table_column=True,
        ),
        "output_directory": LatchParameter(
            display_name="Output Directory",
            description="Directory on LatchBio where the results directory will be sent.",
            batch_table_column=True,  # Show this parameter in batched mode.
        ),
    },
)


@workflow(metadata)
def template_workflow(
    JpgFiles: List[LatchFile],
    output_directory: LatchOutputDir

) -> LatchDir:
    """
    Cherry Pick list of colonies
    """


    return task(
        JpgFiles = JpgFiles,
        output_directory = output_directory
    )