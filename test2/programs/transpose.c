#define N 20

int A[N][N];
int B[N][N];

void transpose() {

    for(int i=0;i<N;i++) {
        for(int j=0;j<N;j++) {
            B[j][i] = A[i][j];
        }
    }

}

int main() {
    transpose();
    return 0;
}