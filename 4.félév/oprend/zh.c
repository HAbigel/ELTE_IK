#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>
#include <unistd.h> // for pipe()
#include <string.h>
#include <sys/wait.h>
#include <time.h>
#include <signal.h>
#include <sys/types.h>
#include <fcntl.h>
#include <sys/ipc.h> 
#include <sys/msg.h> 
#include <wait.h> 
#include <sys/shm.h>
#include <sys/sem.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>


struct Uzenet{ 
    long mtype;//ez egy szabadon hasznalhato ertek, pl uzenetek osztalyozasara
    int db; 
}; 

#define MEMSIZE 1024

// mutex: kozos tarhely, egyszerre csak 1 irhatja, ehhez van a down es az up down a befoglalas, down a kilepes,
// szamafornal meg van adva hogy egyszerre max hanyan hasznalhatjak. eroforraseloszlas
// mi most mutexet fogunk csak hasznalni

int szemafor_letrehozas(const char *pathname, int szemafor_ertek)
{
    int semid;
    key_t kulcs;

    kulcs = ftok(pathname, 1);
    if ((semid = semget(kulcs, 1, IPC_CREAT | S_IRUSR | S_IWUSR)) < 0) // 1 -> hany lehet bent egyszerre
        perror("semget");
    // semget 2. parameter is the number of semaphores
    if (semctl(semid, 0, SETVAL, szemafor_ertek) < 0) // 0= first semaphores // 0 ha fontos ki az elso, 1 ha mindegy ki az elso
        perror("semctl");

    return semid;
}

void szemafor_muvelet(int semid, int op)
{
    struct sembuf muvelet;

    muvelet.sem_num = 0;
    muvelet.sem_op = op; // op=1 up, op=-1 down
    muvelet.sem_flg = 0;

    if (semop(semid, &muvelet, 1) < 0) // 1 number of sem. operations
        perror("semop");
}

void szemafor_torles(int semid)
{
    semctl(semid, 0, IPC_RMID);
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

void AddNewData(int osszHal)
{
    int jelentes = OpenFile("jelentes.txt", O_RDWR | O_CREAT);

    //write(jelentes, &osszHal, sizeof(int));
    if (write(jelentes,&osszHal,sizeof(osszHal))!=sizeof(osszHal)){perror("There is a mistake in writing\n");exit(1);}
    else {printf("Jelentes kesz.\n");}

    close(jelentes);
}

volatile sig_atomic_t readyCount = 0;

void handler(int signumber){
    printf("Ready\n");
    readyCount++;
}

int main(int argc, char* argv[]){
    srand(time(NULL));
    int status;
    int pipeC1toP[2];
    int pipeC2toP[2];
    int pipePtoC1[2];
    int pipePtoC2[2];

    key_t kulcsSema;
    int sh_mem_id, semid;
    char *s;
    kulcsSema = ftok(argv[0], 1);
    sh_mem_id = shmget(kulcsSema, MEMSIZE, IPC_CREAT | S_IRUSR | S_IWUSR);
    s = shmat(sh_mem_id, NULL, 0);
    semid = szemafor_letrehozas(argv[0], 0);

    pipe(pipeC1toP); // ez kell!!!
    pipe(pipeC2toP); // ez kell!!!
    pipe(pipePtoC1); // ez kell!!!
    pipe(pipePtoC2); // ez kell!!!

    int uzenetsor;
    key_t kulcs; 
    kulcs = ftok(argv[0],1); // fajleleresi ut es int es ebbol general egy intet. // hash fv szeruen mukodik, ugyanazokra a parameterekre ugyanaz a kimenet, kulonbozoekre kulonbozoek
    uzenetsor = msgget( kulcs, 0600 | IPC_CREAT ); // a kulcs az id, generalni szoktuk ; jogosultsagok (ittt irasi es olvasasi), letrehozas    
    if ( uzenetsor < 0 ) { 
         perror("msgget"); 
         return 1; 
    } 


    pid_t f1 = fork();
    if (f1<0){perror("The fork calling was not succesful\n"); exit(1);} 
    if (f1>0){
        pid_t f2 = fork();
        if (f2<0){perror("The fork calling was not succesful\n"); exit(1);} 
        if (f2>0){ // parent
            close(pipeC1toP[1]); // close writw
            close(pipeC2toP[1]); // close write
            close(pipePtoC1[0]); // close read
            close(pipePtoC2[0]); // close read


            signal(SIGUSR1, handler);
            while(readyCount<2)
            {
                pause();
            }
            int kellFaDb = 2;
            int kellHalDb = 3;

            struct Uzenet faUz = {5, kellFaDb};
            struct Uzenet halUz = {6, kellHalDb};
            int uzFaStatus;
            int uzHalStatus;
            uzFaStatus = msgsnd( uzenetsor, &faUz, sizeof(int), 0 );
            uzHalStatus = msgsnd( uzenetsor, &halUz, sizeof(int), 0 );

            char vizesfa[256];
            read(pipeC1toP[0], &vizesfa, 256);
            printf( "%s\n", vizesfa ); 

            char jajj[256];
            read(pipeC2toP[0], jajj, 256);
            printf( "%s\n", jajj ); 

            char segits[256];
            sprintf(segits, "Hagyja Béla a vizes fát másnak, segítsen a horgásznak!");
            write(pipePtoC1[1], segits, 256);

            int osszHal;
            read(pipeC2toP[0], &osszHal, sizeof(int));

            sleep(3);
            char vigasz[256];
            sprintf(vigasz, "Miután a csukának nem sikerült Magát megenni, örülök, hogy épségben előkerült." );
            write(pipePtoC2[1], vigasz, 256);

            close(pipeC1toP[0]); // close read
            close(pipeC2toP[0]); // close read
            close(pipePtoC1[1]); // close write
            close(pipePtoC2[1]); // close write

            szemafor_muvelet(semid, -1); // down, wait if necessary
            AddNewData(osszHal);
            szemafor_muvelet(semid, 1); // up
            shmdt(s);
            wait(NULL);
            szemafor_torles(semid);
            shmctl(sh_mem_id, IPC_RMID, NULL);

            waitpid(f1,&status,0); 
            waitpid(f2,&status,0); 
            exit(0);
        }
        else{ // Tutajos hal gyerek 2
            close(pipeC1toP[1]); // close write
            close(pipeC1toP[0]); // close read
            close(pipeC2toP[0]); // close read
            close(pipePtoC1[0]); // close read
            close(pipePtoC1[1]); // close write
            close(pipePtoC2[1]); // close write


            sleep(3);
            kill(getppid(),SIGUSR1);

            struct Uzenet halUz;
            int status;
            status = msgrcv(uzenetsor, &halUz, sizeof(int), 6, 0 );
            printf( "%d db hal kell.\n", halUz.db ); 
            //---------------------------------
            int halDb = (rand()%2)+1;

            char jajj[256];
            sprintf(jajj, "A csuka megfogott stop, segítség stop!");
            write(pipeC2toP[1], jajj, 256);
            // -------------------------------------------------
            int pluszHal = rand()%2;
            int osszHal = halDb + pluszHal;
            write(pipeC2toP[1], &osszHal, sizeof(int));

            sleep(3);
            char vigasz[256];
            read(pipePtoC2[0], vigasz, 256);
            printf( "%s\n", vigasz ); 

            close(pipeC2toP[1]); // close write
            close(pipePtoC2[0]); // close read
            szemafor_muvelet(semid, 1); // up
            sleep(5);
            shmdt(s);

            exit(0);
        }
    }
    else{ // Butyok fa gyerek 1
        close(pipeC2toP[1]); // close write
        close(pipeC2toP[0]); // close read
        close(pipeC1toP[0]); // close read
        close(pipePtoC1[1]); // close write
        close(pipePtoC2[0]); // close read
        close(pipePtoC2[1]); // close write

        sleep(2);
        kill(getppid(),SIGUSR1);

        struct Uzenet faUz;
        int status;
        status = msgrcv(uzenetsor, &faUz, sizeof(int), 5, 0 );
        printf( "%d koteg fa kell.\n", faUz.db ); 
        // ----------------------------------------

        char vizesfa[256];
        sprintf(vizesfa, "Vizes a fa!");
        write(pipeC1toP[1], vizesfa, 256);
        // -------------------------------------
        char segits[256];
        read(pipePtoC1[0], segits, 256);
        printf( "%s\n", segits ); 
   
        close(pipeC1toP[1]); // close write
        close(pipePtoC1[0]); // close read
        szemafor_muvelet(semid, 1); // up
        sleep(5);

        shmdt(s);

        exit(0);
    }

    return 0;
}