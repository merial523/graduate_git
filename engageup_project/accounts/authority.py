from django.urls import reverse_lazy


class AuthoritySet():
    @staticmethod
    #権限を分ける関数　２パターン
    def authority_two(authority_name_1,page_name_1,authority_name_2,page_name_2,rank):
        if rank == authority_name_1:
            return reverse_lazy(f"{authority_name_1}:{page_name_1}")
        elif rank == authority_name_2:
            return reverse_lazy(f"{authority_name_2}:{page_name_2}")

    @staticmethod
    #権限を分ける関数　4パターン
    def authority_four(aut_1,page_1,aut_2,page_2,aut_3,page_3,aut_4,page_4,rank):
        if rank == aut_1:
            return reverse_lazy(f"{aut_1}:{page_1}")
        elif rank == aut_2:
            return reverse_lazy(f"{aut_2}:{page_2}")
        elif rank == aut_3:
            return reverse_lazy(f"{aut_3}:{page_3}")
        elif rank == aut_2:
            return reverse_lazy(f"{aut_4}:{page_4}")
