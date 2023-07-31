from dataclasses import dataclass
from typing import Optional


@dataclass()
class DocumentFile:
    filename: str


@dataclass()
class DocumentEdition:
    files: list[DocumentFile]


@dataclass()
class Document:
    editions: list[DocumentEdition]


@dataclass()
class SoftwareProgram:
    name: str
    program_version: str


@dataclass()
class Software:
    software_id: str
    software_version_id: str
    software_program: list[SoftwareProgram]


@dataclass()
class Process:
    name: str
    description: str
    software: list[Software]


@dataclass()
class ProcessingInformation:
    process: list[Process]


@dataclass()
class DisciplineArea:
    processing_information: ProcessingInformation


@dataclass()
class FileArea:
    file_name: str


@dataclass
class TimeCoordinates:
    start_date: str
    stop_date: str


@dataclass()
class ContextArea:
    time_coordinates: TimeCoordinates


@dataclass()
class ObservationArea:
    time_coordinates: TimeCoordinates


@dataclass()
class ModificationDetail:
    version_id: str
    modification_date: str
    description: str


@dataclass
class ModificationHistory:
    modification_details: list[ModificationDetail]


@dataclass()
class IdentificationArea:
    logical_id: str
    collection_id: str
    version_id: str
    lidvid: str
    major: int
    minor: int
    modification_history: ModificationHistory


@dataclass()
class ProductLabel:
    identification_area: IdentificationArea
    file_area: Optional[FileArea]
    context_area: Optional[ContextArea]
    discipline_area: Optional[DisciplineArea]
    document: Optional[Document]


@dataclass()
class CollectionLabel:
    identification_area: IdentificationArea
    context_area: ContextArea
