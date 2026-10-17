"""
Created: Camden Opfer October 2026

Creates a bib file with standardized entry formating and with entries in author-year ordering from an existing bib file. Once this is done, other functions allow for adding more entries by DOI or by the text of the entry, and for searching through the bib file by keyword.
"""

import re
import datetime
from copy import copy
import webbrowser
import argparse
import requests
import numpy as np
import numpy.typing as npt

allFields = ['address', 'annote', 'author', 'booktitle', 'chapter', 'crossref', 'doi', 'edition', 'editor', 'email', 'howpublished', 'institution', 'journal', 'month', 'note', 'number', 'organization', 'pages', 'publisher', 'school', 'series', 'title', 'type', 'volume', 'year']
surnameParticles = [' auf der ', ' auf ', ' bin ', ' da ', ' de la ', 'de las', ' de los ', ' op de ', ' van de ', ' de ', ' del ', ' della ', ' delle ', ' dello ', ' van den ', ' von den ', ' den ', ' van der ', ' von der ', ' und der ', ' der ', ' di ', ' du ', ' la ', ' las ', ' le ', ' saint ', ' sainte ', ' san ', ' santa ', ' santo ', ' st ', ' st. ', ' ste ', ' und ', ' van het ', ' van ', ' vande ', ' vanden ', ' vander ', ' von '] # Weirdly ordered so that searching for elements in order avoids finding, e.g., ' de ' or ' van ' when really there's a ' van de '
monthToInt = {'01': 1, '1': 1, 'jan': 1, 'january': 1, 'jan.': 1,
          '02': 2, '2': 2, 'feb': 2, 'february': 2, 'feb.': 2,
          '03': 3, '3': 3, 'mar': 3, 'march': 3, 'mar.': 3,
          '04': 4, '4': 4, 'apr': 4, 'april': 4, 'apr.': 4,
          '05': 5, '5': 5, 'may': 5,
          '06': 6, '6': 6, 'jun': 6, 'june': 6, 'jun.': 6,
          '07': 7, '7': 7, 'jul': 7, 'july': 7, 'jul.': 7,
          '08': 8, '8': 8, 'aug': 8, 'august': 8, 'aug.': 8,
          '09': 9, '9': 9, 'sep': 9, 'sept': 9, 'september': 9, 'sep.': 9, 'sept.': 9,
          '10': 10, 'oct': 10, 'october': 10, 'oct.': 10,
          '11': 11, 'nov': 11, 'november': 11, 'nov.': 11,
          '12': 12, 'dec': 12, 'december': 12, 'dec.': 12}

# Ordered fields for each entry type. If other fields in the allFields list are provided, they will be added after these in alphabetical order. See examples of each entry type and lists of what fields are required/optional at https://bibtex.eu/types and https://www.bibtex.com/e/entry-types/
articleFields = ['title', 'author', 'journal', 'publisher', 'volume', 'number', 'pages', 'year', 'month', 'doi']
bookFields = ['title', 'author', 'publisher', 'address', 'edition', 'year', 'month', 'doi', 'issn', 'isbn']
bookletFields = ['title', 'author', 'howpublished', 'editor', 'organization', 'address', 'volume', 'number', 'series', 'year', 'month']
conferenceFields = ['title', 'booktitle', 'author', 'editor', 'organization', 'publisher', 'address', 'volume', 'number', 'pages', 'series', 'year', 'month']
inbookFields = ['title', 'booktitle', 'author', 'editor', 'publisher', 'address', 'volume', 'number', 'pages', 'edition', 'series', 'year', 'month']
incollectionFields = ['title', 'booktitle', 'author', 'editor', 'publisher', 'address', 'volume', 'number', 'pages', 'series', 'year', 'month']
inproceedingsFields = ['title', 'booktitle', 'author', 'editor', 'organization', 'volume', 'number', 'pages', 'series', 'year', 'month']
manualFields = ['title', 'author', 'organization', 'edition', 'year', 'month'] # NOTE author is optional for this type, which would break some code later on
mastersthesisFields = ['title', 'author', 'school', 'address', 'type', 'year', 'month']
miscFields = [] # NOTE This type is ignored for now because it has no field requirements. It is usually used to cite a website, but is very, very flexible. Probably not worth making the code here flexible enough to deal with that.
phdthesisFields = mastersthesisFields
proceedingsFields = ['title', 'editor', 'publisher', 'address', 'volume', 'number', 'series', 'year', 'month'] # NOTE author is not allowed for this type, which would break some code below
techreportFields = ['title', 'author', 'institution', 'number', 'year', 'month', 'doi']
unpublishedFields = articleFields # NOTE The unpublished type can really be used for any unpublished work, but since it's most common for articles, that is assumed here. This could break code

fieldsByEntryType = {
    'article': articleFields, 'book':bookFields, 'booklet':bookletFields, 'conference':conferenceFields,
    'inbook':inbookFields, 'incollection':incollectionFields, 'inproceedings':inproceedingsFields,
    'manual':manualFields, 'mastersthesis':mastersthesisFields, 'misc':miscFields, 'phdthesis':phdthesisFields,
    'proceedings':proceedingsFields, 'techreport':techreportFields, 'unpublished':unpublishedFields
    }

def handleAuthor(authorIn: str) -> tuple[str, str]:
    """
    Standardize the format of the author field and provide a string to use at the start of the entry title (the other part being the year). Author order is preserved, since it is intended to show seniority/degree of contribution.
    """
    # TODO Handle special characters (letters with accents, umlauts, etc.), replacing them with LaTeX versions of the accent. Maybe make a dictionary where letters map to themselves and special characters go like {...,'ë': '{\"e}',...}

    def getEntryTitleAuthor(authorOut: str) -> str:
        def getLastName(author: str) -> str:
            last, _ = author.split(', ')
            last = last.lower()
            last = re.sub('[^a-z]','', last) # Take only alphabetic characters. No whitespace or special characters related to accents
            return last

        finalAuthors = authorOut.split(' and ')

        if len(finalAuthors) == 1:
            return getLastName(finalAuthors[0])
        if len(finalAuthors) == 2:
            last0 = getLastName(finalAuthors[0])
            last1 = getLastName(finalAuthors[1])
            return last0 + '-' + last1
        return getLastName(finalAuthors[0]) + '-et'

    # English 'and'/'AND' is used by bibtex/biber regardless the language of the user
    rawAuthors = re.split(' and ', authorIn, flags=re.IGNORECASE)

    # There are three allowable ways to write an author's name:
    # "First particle Last" "particle Last, First" "particle Last, Jr, First"
    # All are handled here, with the second or third used for output depending on the complexity of the name
    authorOut = ''
    for author in rawAuthors:
        author.strip() # Remove leading/trailing whitespace
        if ',' not in author: # Input uses "First particle Last" format
            names = author.split(' ')
            if len(names) < 2:
                raise ValueError(f"Author field text '{author}' cannot be parsed into first and last names. Correct input bib file and try again.")

            for particle in surnameParticles:
                if particle in author: # Mishandles edge case where someone has two of the same particle. Seems unlikely to happen though
                    first, last = author.split(particle)
                    author = particle.strip() + ' ' + last + ', ' + first
                    break
            else:
                author = names[0] + ', '
                for name in names[1:]:
                    author += name + ' '
                author = author[:-1] # Remove last space

        authorOut += author + ' and '

    authorOut = authorOut[:-5] # Remove final ' and '

    return authorOut, getEntryTitleAuthor(authorOut)

def handleDoi(doiIn: str, rootDoi: str|None = None) -> str:
    """
    Strips starting 'https://doi.org/', 'doi.org/', or similar url as needed. Optionally, adds one of these preambles consistently.
    """
    doiOut = copy(doiIn)
    if doiOut[:8] == 'https://':
        doiOut = doiOut[8:]
    elif doiOut[:7] == 'http://':
        doiOut = doiOut[7:]
    if doiOut[:8] == 'doi.org/':
        doiOut = doiOut[8:]

    if rootDoi is not None:
        doiOut = rootDoi + doiOut

    return doiOut

def handleField(fields: list[str], fieldName: str):
    """
    Does some final modification to fields that require it. For example, makes author name formatting and DOI URL style more consistent. Also adds {} around fields that need them (e.g. author, title) and foregoes them around numbers (e.g. year '2010' or volume '2')
    """
    if fieldName == 'author':
        author, _ = handleAuthor(fields['author'])
        return f'{{{author}}}'

    if fieldName == 'doi':
        try:
            rawDoi = fields['doi']
        except KeyError:
            return None
        doi = handleDoi(rawDoi)
        return f'{{{doi}}}'

    if fieldName == 'month':
        try:
            rawMonth = fields['month']
        except KeyError:
            return None
        try:
            niceMonth = monthToInt[rawMonth.lower()]
        except KeyError as k:
            raise ValueError(f'Invalid month argument {rawMonth} encountered. Please fix the input to handleField().') from k
        return niceMonth

    if fieldName == 'journal':
        try:
            rawJournal = fields['journal']
        except KeyError:
            return None

        rawJournal.replace(' &amp; ', ' and ') # Journal like "Agriculture, Ecosystems, & Environment" may have & in name that breaks LaTeX
        # TODO Catch other special characters, and maybe repeat this for other fields? Not sure what else will realistically get thrown in

    try:
        field = fields[fieldName]
    except KeyError:
        return None

    if field.isdigit(): # field is completely a number, like a year of publication 2010. No need to enclose in {}
        return field

    return f'{{{field}}}'

def getEntryType(entry: str) -> str:
    """
    Returns the string that determines an entry's type. For example, 'article', 'book', or 'techreport'.
    """
    inEntryType = False
    entryType = ''
    for char in entry:
        if not inEntryType:
            if char == '@':
                inEntryType = True
            if char == '%':
                break
        else:
            if char == '{':
                break
            entryType += char
        entryType = entryType.lower().strip() # Lowercase, no leading/trailing whitespace
    return entryType

def getFields(entry:str) -> dict[str]:
    """
    Creates a dictionary where each key is a field name (e.g. 'title', 'author', or 'year') and the corresponding value is the text that belongs in that field
    """
    fields = {}
    for field in allFields:
        fieldSpacing = re.search(f'{field}\\s*=', entry)
        if fieldSpacing is None: # This field is not found in the provided entry
            continue
        _, fieldStart = fieldSpacing.span()

        quoteMarks, openBrackets, closedBrackets = 0, 0, 0
        fieldText = ''
        for char in entry[fieldStart:]:
            if char == '"' and openBrackets == closedBrackets:
                quoteMarks += 1
            elif char == '{':
                if quoteMarks > 0 or openBrackets > 0:
                    fieldText += char
                openBrackets += 1
            elif char == '}':
                if quoteMarks > 0 or closedBrackets + 1 < openBrackets:
                    fieldText += char
                else:
                    break
                closedBrackets += 1
            elif char == ',' and quoteMarks == 0 and openBrackets == 0 and closedBrackets == 0:
                break
            else:
                fieldText += char

            if quoteMarks == 2:
                break

        # Cut down on whitespace
        fieldText = fieldText.strip()
        fieldText = ' '.join(fieldText.split()) # str.split() defaults to splitting around whitespace, so reduces arbitrary whitespace (' ', '\n  ', or '\t\n  \n  ') to single space (' ')

        fields[field] = fieldText
    return fields

def getEntryInfo(entry: str) -> tuple[str, str, dict[str]]:
    """
    Separate an entry into its type (article, report, book, etc) and a dictionary containing the provided fields.

    Since '=' and ',' are allowed within the value for a field, this function is awfully tedious
    """
    entryType = getEntryType(entry)
    fields = getFields(entry)

    # Get planned entry title
    _, entryTitleAuthor = handleAuthor(fields['author'])
    try:
        entryTitle = entryTitleAuthor + '_' + fields['year']
    except KeyError:
        entryTitle = entryTitleAuthor + '_' + 'nd'

    return entryType, entryTitle, fields

def findEntries(bibFilePath: str) -> list[tuple[int,int]]:
    """
    Creates a list of tuples, where the elements of each tuple are the start and end points of a bibEntry. This allows operation on only one entry at a time, so that a massive bib file can be handled without huge active memory usage.
    """
    entryInds = []
    inEntry = False
    openBrackets, closedBrackets = 0, 0

    try:
        with open(bibFilePath, 'r', encoding='UTF-8') as file:
            for i, line in enumerate(file):
                if not inEntry and '@' in line:
                    for char in line:
                        if char == '@':
                            start = i
                            inEntry = True
                            break
                        if char == '%':
                            break
                if inEntry:
                    openBrackets += line.count('{')
                    closedBrackets += line.count('}')
                    if openBrackets == closedBrackets:
                        entryInds.append((start, i))
                        inEntry = False
                        openBrackets, closedBrackets = 0, 0

    except FileNotFoundError as e:
        raise FileNotFoundError(f"FileNotFound Error for path '{bibFilePath}'") from e

    return entryInds

def getEntries(path: str) -> tuple[list[str], list[tuple[int,int]]]:
    """
    Searches through an existing file to find the existing entries, returning their eventual "keys" (names for the entries, called titles here to avoid confusion with Python dicts) and the lines in the old file that they span.
    """
    entryBoundPairs = findEntries(path)
    if not entryBoundPairs:
        raise ValueError(f'No valid bib entries found in file {entryBoundPairs}')

    with open(path, 'r', encoding='UTF-8') as oldFile:
        oldLines = oldFile.readlines()
        entryTitles = []
        for entryBoundPair in entryBoundPairs:
            entryLines = oldLines[entryBoundPair[0]:entryBoundPair[1]]
            entryStr = ' '.join(entryLines)
            _, entryTitle, _ = getEntryInfo(entryStr)
            entryTitles.append(entryTitle)

    return entryTitles, entryBoundPairs

def sortEntryTitles(titles: list[str]) -> tuple[npt.NDArray, npt.NDArray]:
    """
    Sort entry titles in author year order in the format "<author>_<year>", "<author1>-<author2>_<year>", or "<author1>-et_<year>" depending on how many authors are listed
    """
    # Sort provided titles
    titlePieces = np.zeros((len(titles),3), dtype=np.dtype('U20')) # U20 type is 20-character string. Since this is only used for sorting, this may incorrectly sort two similar, very long names. But unlikely to be an issue
    for i, title in enumerate(titles):
        authorPiece, yearPiece = title.split('_')
        authorPieces = authorPiece.split('-') + [''] # Adding '' means things with one author (title like smith_2020) are sorted first
        titlePieces[i] = [authorPieces[0], authorPieces[1], yearPiece]
    titlePieces[titlePieces[:,1] == 'et', 1] = 'zzzzzzzz' # Forces et al papers being sorted last
    sortInds = np.lexsort([titlePieces[:,2], titlePieces[:,1], titlePieces[:,0]])

    sortedTitles = np.array(titles)[sortInds]

    # Add '_0', '_1', '_2', etc. to the end of entries which match in author/year. Avoids duplicates
    sortedTitlePieces = titlePieces[sortInds]
    repeatMask = np.all(sortedTitlePieces[1:] == sortedTitlePieces[:-1], axis=1)
    repeatIdentifiers = np.zeros(np.sum(repeatMask), dtype=str)

    identifier = 0
    for repeatBool in repeatMask:
        if repeatBool:
            repeatIdentifiers = f'_{identifier}'
            identifier += 1
        else:
            identifier = 0

    sortedTitles[1:][repeatMask] = np.char.add(sortedTitles[1:][repeatMask], repeatIdentifiers)

    return sortedTitles, sortInds

def niceifyEntry(entry: str, entryTitle: str|None = None) -> str:
    """
    Returns a standardized string of a provided entry. The entryTitle argument can be optionally be provided to override the default (useful when adding a unique identifier to avoid repeats)
    """
    entryType, defaultEntryTitle, fields = getEntryInfo(entry)

    if entryTitle is None:
        entryTitle = defaultEntryTitle

    entryType = entryType.lower()

    remainingFields = copy(allFields)

    niceEntry = f'@{entryType}{{{entryTitle}'
    try:
        expectedFields = fieldsByEntryType[entryType]
    except KeyError as e:
        raise NotImplementedError(f'Can only do "article" type entries for now. You\'ll have to modify "niceifyEntry()" to add {entryType}') from e

    for expectedField in expectedFields: # This is how fields are consistently ordered, always following "expectedFields" for the entry type
        field = handleField(fields, expectedField)
        if field is not None:
            niceEntry += f',\n {expectedField: <10}= {field}'

        remainingFields.remove(expectedField)

    for remainingField in remainingFields:
        field = handleField(fields, remainingField)
        if field is not None:
            niceEntry += f',\n {remainingField: <10}= {field}'

    niceEntry += '\n}'

    return niceEntry

def niceifyBib(oldPath: str, newPath: str|None = None):
    """
    Copies the bibliography entries of oldFile into newFile, but with standardized formatting and organization into alphabetical order
    """
    if newPath is None:
        newPath = oldPath[:-4] + '_butNicer.bib'
    print(f'Creating nice bib file {newPath} from {oldPath}')

    print('Getting list of bib entries...')
    entryTitles, oldEntryBoundPairs = getEntries(oldPath)

    print('Sorting entries alphabetically by title...')
    sortedTitles, indexMap = sortEntryTitles(entryTitles)
    sortedBoundPairs = np.array(oldEntryBoundPairs)[indexMap]

    print('Writing out new bib file')
    with open(newPath, 'w', encoding='UTF-8') as newFile:
        todayDt = datetime.datetime.today()
        newFile.write(f'% Bib file created on {todayDt.day} {todayDt.strftime('%b')}, {todayDt.year} by bibFileNiceifier.py from existing file at {oldPath}')

    for entryBoundPair, title in zip(sortedBoundPairs, sortedTitles):
        with open(oldPath, 'r', encoding='UTF-8') as oldFile:
            oldLines = oldFile.readlines()
            entryLines = oldLines[entryBoundPair[0]:entryBoundPair[1]]
            entryStr = ' '.join(entryLines)

        niceEntry = niceifyEntry(entryStr, title)
        with open(newPath, 'a', encoding='UTF-8') as newFile:
            newFile.write('\n\n' + niceEntry)

def getBibFromApi(doi:str, baseUrl:str = 'http://api.crossref.org/', timeout:int|float = 3):
    """
    Fetches a bib item of the relevant doi from a library at the baseUrl. The get call will timeout after the specified number of seconds (default 3sec).
    """
    url = f'{baseUrl}works/{doi}/transform/application/x-bibtex'

    r = requests.get(url, timeout=timeout)
    if r.status_code != 200:
        raise requests.ConnectionError(f'Unable to fetch bib item from url {url}')

    bib = r.content
    bib = str(bib, "utf-8")

    bib = bib[:-2] + f', doi={{{doi}}} }}'

    return bib

def addToBibFile(fname:str, doi:str|None = None, rawBibItem:str|None = None, printConfirmation:bool=True, **kwargs):
    """
    Adds an entry corresponding to either the provided DOI or using the bib item provided (usefull when an entry doesn't have a DOI, but you can download/construct a bibtex entry some other way)
    """
    if (doi is None and rawBibItem is None) or not (doi is None or rawBibItem is None):
        raise ValueError('Must specify exactly one of "doi" and "rawBibItem" in call of addToBibFile()')

    if doi:
        searchDoi = handleDoi(doi, None)
        with open(fname, 'r', encoding='UTF-8') as f:
            entryName = None
            for line in f:
                if '@' in line:
                    startInd = line.index('{') + 1
                    endInd = line.index(',')
                    entryName = line[startInd:endInd]
                if searchDoi in line:
                    if entryName is None:
                        raise ValueError(f'The file {fname} contains the doi {searchDoi} before any entry header, so it is unclear if it does or does not exist as an entry already.')

                    print(f'Entry with DOI {searchDoi} already exists with name {entryName} in file {fname}. Will not add that entry.')
                    return

        rawBibItem = getBibFromApi(doi, **kwargs)

    niceEntry = niceifyEntry(rawBibItem)
    fields = getFields(niceEntry)

    if rawBibItem is not None and 'doi' in fields:
        searchDoi = handleDoi(fields['doi'], None)
        with open(fname, 'r', encoding='UTF-8') as f:
            for line in f:
                if searchDoi in line:
                    print(f'Entry with DOI {searchDoi} already exists in file {fname}. Will not add that entry.')
                    return

    _, entryTitleAuthor = handleAuthor(fields['author'])
    newEntryTitle = entryTitleAuthor + '_' + fields['year']

    etReplacement = '-zzzzz'
    if '-et_' in newEntryTitle:
        sortTitle = newEntryTitle.split('-')[0] + etReplacement + '_' + newEntryTitle.split('_')[1]
    else:
        sortTitle = newEntryTitle

    existingEntryTitles, existingEntryBoundPairs = getEntries(fname)

    placementLine = existingEntryBoundPairs[0][0]
    identifier = -1
    for existingTitle, existingBoundPair in zip(existingEntryTitles, existingEntryBoundPairs):
        if '-et_' in existingTitle:
            existingTitle = existingTitle.split('-')[0] + etReplacement + '_' + existingTitle.split('_')[1]

        if sortTitle < existingTitle:
            placementLine = existingBoundPair[0]
            break
        if sortTitle == '_'.join(existingTitle.split('_')[:2]): # Ignores if the existingTitle already has an identifier
            identifier += 1
    else: # This is the new last entry
        placementLine = -1 # TODO Fix this so that the spacing is actually nice. Maybe just append to the file? Would be faster at least

    if identifier >= 0:
        newEntryTitle += f'_{identifier}'

    niceEntry = niceifyEntry(rawBibItem, newEntryTitle)

    with open(fname, 'r', encoding='UTF-8') as f:
        lines = f.readlines()
    # outLines = lines[:placementLine] + [f'\n{niceEntry}\n'] + lines[placementLine:]
    outLines = lines[:placementLine] + [f'{niceEntry}\n\n'] + lines[placementLine:]
    with open(fname, 'w', encoding='UTF-8') as f:
        f.writelines(outLines)

    if printConfirmation:
        print(f'Added bib entry for DOI {doi} as {newEntryTitle}')

    return newEntryTitle

def bibQuery(fname:str, bibItemName:str, webOpen:bool=True) -> tuple[str, str]:
    """
    Print and return the DOI and LibKey URLs associated with a bib item within a bib file located at fname. If webOpen is True, also opens the LibKey URL in the default browser.
    """
    inCorrectItem = False
    with open(fname, 'r', encoding='UTF-8') as f:
        for line in f:
            if bibItemName in line:
                inCorrectItem = True
            if inCorrectItem and 'doi' in line:
                startInd = line.index('{') + 1
                endInd = line.index('}')
                doi = line[startInd:endInd]
                break
        else:
            raise ValueError(f'Entry {bibItemName} not found in bib file {fname}')

    url_doi = f'https://{doi}'
    url_libKey = f'https://libkey.io/libraries/498/{doi}'

    if webOpen:
        webbrowser.open(url_libKey, new=2)

    print(f'DOI: {url_doi}\nLibKey: {url_libKey}')
    return url_doi, url_libKey

def main():
    """
    Arbitrates what the script does. See argparse help for more details.
    """
    parser = argparse.ArgumentParser(description='Create nice bib files, or add new entries to an existing bib file by DOI(s) or bib item(s)')
    parser.add_argument("bibFile", help="Path to main bib file")
    group = parser.add_mutually_exclusive_group(required=True) # One, and only one, argument within the group is required
    group.add_argument("--doi", help="A DOI (or sequence of DOIs) to add to the main bib file", nargs='+')
    group.add_argument("--bibItem", help="A full bib item to add to the main bib file")
    group.add_argument("--entryKeyword", help="The keyword of an entry in the main bib file. The DOI of this entry will be looked up, and it will be opened in a browser alond with being printed to the terminal.")
    group.add_argument("--outBibFile", help="Path to which a niceified version of bibFile will be written")
    args = parser.parse_args()

    if isinstance(args.doi, str):
        addToBibFile(args.bibFile, args.doi)
    elif isinstance(args.doi, list):
        for singleDoi in args.doi:
            addToBibFile(args.bibFile, singleDoi)

    elif args.bibItem:
        addToBibFile(args.bibFile, rawBibItem=args.bibItem)

    elif args.entryKeyword:
        bibQuery(args.bibFile, args.entryKeyword)

    elif args.outBibFile:
        niceifyBib(args.bibFile, args.outBibFile)

    else:
        # Use of mutually exclusive group in arg parsing should avoid this ever being triggered
        raise ValueError('Expected at least one argument specifying operation to perform')

if __name__ =='__main__':
    ## Test niceifying of existing bib file
    # testPath = r'C:\Users\User\WS\ugly.bib'
    # niceifyBib(testPath)

    ## Test basic adding to a file
    # fileToAddTo = r'C:\Users\User\WS\ugly_butNicer.bib'
    # doiToAdd = 'https://doi.org/10.1126/science.7041255'
    # print(getBibFromApi(addCitation))
    # addToBibFile(fileToAddTo, doiToAdd)

    ## Test title-making when multiple papers have the same author (li et al.) and year (2020)
    # fileToAddTo = r'C:\Users\User\WS\ugly_butNicer.bib'
    # li1 = '10.1016/j.meegid.2020.104285'
    # li2 = '10.1109/TSMC.2018.2867532'
    # li3 = '10.1098/rsif.2020.0135'
    # for liDoi in [li1, li2, li3]:
    #     addToBibFile(fileToAddTo, liDoi)

    ## Actual use
    # thesisBib = r'C:\Users\User\WS\Opfer-Masters-Thesis\opfer_thesis.bib'
    # thesisBib = '/home/camden/Files/ComputationalClimate/Thesis/Opfer-Masters-Thesis/opfer_thesis.bib'

    # niceifyBib(thesisBib)

    # doiToAdd = '10.1038/s41467-022-29601-0'
    # addedTitle = addToBibFile(thesisBib, doi=doiToAdd)

    # entryToAdd = '''Entry Here'''
    # addedTitle = addToBibFile(thesisBib, rawBibItem=entryToAdd)

    # entryToLookup = 'harris-et_2021'
    # bibQuery(thesisBib, entryToLookup)

    main()
