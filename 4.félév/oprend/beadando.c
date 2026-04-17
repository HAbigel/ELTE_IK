#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <errno.h>
#include <unistd.h>
#include <string.h>

typedef struct{
    char termohely[50];
    char tabla[50];
    char tipus[50];
    int meret;
    int pusztitasmerteke;
} Datarow;

void ListDatabase(int database);

Datarow AskForData()
{
    Datarow newData;
    printf("\nTermőhely: ");

    getchar();
    fgets(newData.termohely, 50, stdin);
    newData.termohely[strcspn(newData.termohely, "\n")] = 0;

    printf("Tábla: ");
    fgets(newData.tabla, 50, stdin);
    newData.tabla[strcspn(newData.tabla, "\n")] = 0;

    printf("Típus: ");
    fgets(newData.tipus, 50, stdin);
    newData.tipus[strcspn(newData.tipus, "\n")] = 0;

    printf("Terület mérete (négyszögölben): ");
    scanf("%d", &newData.meret);

    printf("Pusztítás mértéke (%%-ban): ");
    scanf("%d", &newData.pusztitasmerteke);

    return newData;
}

void PrintDatarow(int i, Datarow* row)
{
    printf("%d. %s, %s, %s, %d négyszögöl, %d%%\n", i, row->termohely, row->tabla, row->tipus, row->meret, row->pusztitasmerteke);
}

int OpenFile(const char* filename, int flags)
{
    int dataFile = open(filename, flags, S_IRUSR | S_IWUSR);
    if (dataFile < 0) {
        perror("open");
        exit(1);
    }
    return dataFile;
}

void AddNewData()
{
    int database = OpenFile("adatok.txt", O_RDWR | O_CREAT | O_APPEND);

    printf("Add meg a következő adatokat: ");
    Datarow newData = AskForData();

    ssize_t bytesWritten = write(database, &newData, sizeof(newData));

    close(database);
}

void ModifyData()
{
    int database = OpenFile("adatok.txt", O_RDWR | O_CREAT);

    int rowToModify;

    ListDatabase(database);
    printf("Válaszd ki melyik sort szeretnéd módosítani: ");
    scanf("%d", &rowToModify);

    printf("\nAdd meg a módosított adatokat:");
    Datarow modifiedData = AskForData();

    off_t offset = (rowToModify-1) * sizeof(Datarow);
    lseek(database, offset, SEEK_SET);

    write(database, &modifiedData, sizeof(Datarow));

    close(database);
}

void DeleteData()
{
    int oldDatabase = OpenFile("adatok.txt", O_RDONLY);
    int newDatabase = OpenFile("temporary.txt", O_WRONLY | O_CREAT | O_TRUNC);
    int rowToDelete;

    ListDatabase(oldDatabase);
    lseek(oldDatabase, 0, SEEK_SET);
    printf("Válaszd ki melyik sort szeretnéd törölni: ");
    scanf("%d", &rowToDelete);

    Datarow row;
    int i = 0;
    while (read(oldDatabase, &row, sizeof(Datarow)) == sizeof(Datarow)) {
        if (i != (rowToDelete - 1)) { 
            write(newDatabase, &row, sizeof(Datarow));
        }
        i++;
    }

    close(oldDatabase);
    close(newDatabase);

    remove("adatok.txt");
    rename("temporary.txt", "adatok.txt");
}

void ListDatabase(int database)
{
    Datarow row;
    int i = 1;

    lseek(database, 0, SEEK_SET);

    while(read(database, &row, sizeof(Datarow)) == sizeof(Datarow)) {
        PrintDatarow(i, &row);
        i++;
    }
}

void List()
{
    int database = OpenFile("adatok.txt", O_RDONLY);

    ListDatabase(database);
    close(database);
}

int MatchSite(Datarow* row, const char* value)
{
    return strcmp(row->termohely, value) == 0;
}

int MatchType(Datarow* row, const char* value)
{
    return strcmp(row->tipus, value) == 0;
}

void Filter(int (*match)(Datarow*, const char*), const char* filterparameter)
{
    int database = OpenFile("adatok.txt", O_RDONLY);
    Datarow row;

    lseek(database, 0, SEEK_SET);

    int i = 1;
    while(read(database, &row, sizeof(Datarow)) == sizeof(Datarow)) {
        if( match(&row, filterparameter) != 0)
        {
            PrintDatarow(i, &row);
            i++;
        }    
    }

    close(database);
}

void FilterBySite()
{
    char chosenSite[50];

    printf("Add meg melyik termőhely adatait szeretnéd látni: ");
    scanf("%s", chosenSite);

    Filter(MatchSite, chosenSite);
}

void FilterByType()
{
    char chosenType[50];

    printf("Add meg melyik szőlőtpus adatait szeretnéd látni: ");
    scanf("%s", chosenType);

    Filter(MatchType, chosenType);
}

int main()
{
    int taskType;
    do
    {
        printf("\nOpciók:\n");
        printf("0 - Kilépés\n");
        printf("1 - Új adat bevitele\n");
        printf("2 - Módosítás\n");
        printf("3 - Törlés\n");
        printf("4 - Listázás\n");
        printf("5 - Szűrés termőhely szerint\n");
        printf("6 - Szűrés fajta szerint\n");
        printf("Feladattípus: ");
        scanf("%d", &taskType);
        printf("\n");

        switch (taskType) {
            case 1: AddNewData(); break;
            case 2: ModifyData(); break;
            case 3: DeleteData(); break;
            case 4: List(); break;
            case 5: FilterBySite(); break;
            case 6: FilterByType(); break;
        }
    } while (taskType != 0);
     
    return 0;
}