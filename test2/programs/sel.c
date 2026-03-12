#define N 50

int arr[N];

void init() {
    for(int i=0;i<N;i++)
        arr[i] = N-i;
}

void selection_sort() {
    for(int i=0;i<N-1;i++) {
        int min=i;

        for(int j=i+1;j<N;j++) {
            if(arr[j] < arr[min])
                min=j;
        }

        int t=arr[i];
        arr[i]=arr[min];
        arr[min]=t;
    }
}

int main(){
    init();
    selection_sort();
    return 0;
}